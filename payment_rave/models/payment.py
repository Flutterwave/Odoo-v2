# coding: utf-8

import logging
import requests
import pprint
import json

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError
from requests.exceptions import HTTPError
from odoo.tools import consteq
from odoo.tools.safe_eval import safe_eval
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class PaymentAcquirerRave(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('rave', 'Rave')], ondelete={'rave': 'cascade'})
    rave_public_key = fields.Char(
        required_if_provider='rave', groups='base.group_user')
    rave_secret_key = fields.Char(
        required_if_provider='rave', groups='base.group_user')
    rave_secret_hash = fields.Char(
        required_if_provider='rave', groups='base.group_user')
    environment = fields.Char(
        required_if_provider='rave', groups='base.group_user')

    @api.model
    def _get_rave_api_url(self):
        """ Flutterwave Base Url"""
        return 'api.flutterwave.com/v3'

    def rave_form_generate_values(self, tx_values):
        self.ensure_one()
        rave_tx_values = dict(tx_values)
        temp_rave_tx_values = {
            'company': self.company_id.name,
            'amount': tx_values['amount'],  # Mandatory
            'currency': tx_values['currency'].name,  # Mandatory anyway
            'currency_id': tx_values['currency'].id,  # same here
            # Any info of the partner is not mandatory
            'address_line1': tx_values.get('partner_address'),
            'address_city': tx_values.get('partner_city'),
            'address_country': tx_values.get('partner_country') and tx_values.get('partner_country').name or '',
            'email': tx_values.get('partner_email'),
            'address_zip': tx_values.get('partner_zip'),
            'name': tx_values.get('partner_name'),
            'phone': tx_values.get('partner_phone'),
        }

        rave_tx_values.update(temp_rave_tx_values)
        return rave_tx_values

    def _handle_rave_webhook(self, data, flutterwave_secret_hash):
        _logger.info("webhook handler initiated...")
        # _logger.info("recieved_hash:\n%s", pprint.pformat(flutterwave_secret_hash))
        reference = data.get("tx_ref")
        # _logger.info("recieved_tx_ref:\n%s", pprint.pformat(reference))
        try:
            return self._flutterwave_handle_checkout_webhook(data, flutterwave_secret_hash)
        except ValidationError as e:
            _logger.info(
                'Received notification for tx %s. Skipped it because of %s', reference, e)
            return False

    def _flutterwave_handle_checkout_webhook(self, hook_object: dir, recieved_hash):
        """
        :param hook_object: provided in the request body
        :return: True if and only if handling went well, False otherwise
        :raises ValidationError: if input isn't usable
        """
        tx_reference = hook_object.get('tx_ref')
        data = {'reference': tx_reference}
        _logger.info("prepared_tx_reference:\n%s", pprint.pformat(data))
        try:
            odoo_tx = self.env['payment.transaction']._rave_form_get_tx_from_data(
                data)
        except ValidationError as e:
            _logger.info(
                'Received notification for tx %s. Skipped it because of %s', tx_reference, e)
            return False

        # check that the secret_hash is valid and notification is indeed from flutterwave.
        PaymentAcquirerRave._verify_flutterwave_signature(
            odoo_tx.acquirer_id, recieved_hash)

        _logger.info("flw odoo_tx: %s" % (pprint.pformat(odoo_tx)))

        # check if the transaction is still pending or status is still draft.
        flutterwave_tx = PaymentTransactionRave._rave_verify_charge(odoo_tx, hook_object)

        return odoo_tx.form_feedback(data, 'rave')

    def _verify_flutterwave_signature(self, recieved_hash):
        """
        :return: true if and only if signature matches hash of payload with local secret hash
        :raises ValidationError: if signature doesn't match
        """
        if not self.rave_secret_hash:
            raise ValidationError(
                'webhook event received but webhook secret is not configured')

        # _logger.info("recieved sign:\n%s", pprint.pformat(recieved_hash))
        # _logger.info("recieved sign:\n%s",
        #              pprint.pformat(self.rave_secret_hash))

        if not consteq(self.rave_secret_hash, recieved_hash):
            _logger.error(
                'incorrect webhook signature from Flutterwave, check if the webhook signature '
                'in Odoo matches to one in the Flutterwave dashboard')
            raise ValidationError('incorrect webhook signature')

        return True


class PaymentTransactionRave(models.Model):
    _inherit = 'payment.transaction'

    def _rave_verify_charge(self, data):
        # https://api.flutterwave.com/v3/transactions/verify_by_reference

        retryCount = 0

        if 'cancelled' == data.get('status'):
            return self._rave_validate_tree(None, data)

        api_url_charge = 'https://%s/transactions/verify_by_reference' % (
            self.acquirer_id._get_rave_api_url())

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % (self.acquirer_id.rave_secret_key)
        }

        params = {
            'tx_ref': self.reference
        }

        _logger.info('_rave_verify_charge: Sending values to URL %s, values:\n%s',
                     api_url_charge, pprint.pformat(params))
        r = requests.get(api_url_charge, headers=headers, params=params)

        if r.status_code >= 500:
            while r.status_code >= 500 and retryCount >= 3:
                retryCount = retryCount + 1
                r = requests.get(api_url_charge, headers=headers, params=params)
            try:
                r.raise_for_status()
            except HTTPError:
                _logger.error(resp.text)
                flutterwave_error = r.json().get('error', {}).get('message', '')
                error_msg = " " + (_("Flutterwave gave us the following info about the problem: '%s'", flutterwave_error))
                raise ValidationError(error_msg)
        # res = r.json()
        _logger.info('_rave_verify_charge: Values received:\n%s',
                     pprint.pformat(r))
        return self._rave_validate_tree(r.json(), data)

    def _rave_validate_tree(self, tree, data):
        self.ensure_one()
        if self.state not in ['draft', 'error', 'pending' ]:
            _logger.info(
                'Flutterwave: trying to validate an already validated tx (ref %s)', self.reference)
            return True

        if 'cancelled' == data.get('status') and tree == None:
            self.sudo().write({
                'state_message': "The Customer cancelled the payment",
                'date': fields.datetime.now(),
            })
            self._set_transaction_cancel()
            return False

        status = tree.get('status')

        # must be error information from the payment modal
        if 'error' == status and data['tx_ref'] != None:
            error = data['processor_response']
            _logger.warn(error)
            self.sudo().write({
                'state_message': error,
                'acquirer_reference': data["flw_ref"],
                'date': fields.datetime.now(),
            })
            self._set_transaction_error(error)
            return False

        amount = tree.get('data').get('amount')
        currency = tree.get('data').get('currency')
        actual_status = tree.get('data').get('status')
        processor_reponse = tree.get('data').get('processor_response')

        if 'success' == status:
            if 'successful' == actual_status and amount == data["amount"] and currency == data["currency"]:
                self.write({
                    'state_message': processor_reponse,
                    'date': fields.datetime.now(),
                    'acquirer_reference': tree["data"]["flw_ref"],
                })
                self._set_transaction_done()
                self.execute_callback()
                if self.payment_token_id:
                    self.payment_token_id.verified = True
                return True
            if 'failed' == actual_status:
                error = processor_reponse
                self.sudo().write({
                    'state_message': processor_reponse,
                    'acquirer_reference': tree["data"]["flw_ref"],
                    'date': fields.datetime.now(),
                })
                self._set_transaction_error(error)
                return False
            if actual_status in ('pending', 'processing'):
                error = processor_reponse
                self.sudo().write({
                    'state_message': processor_reponse,
                    'acquirer_reference': tree["data"]["flw_ref"],
                    'date': fields.datetime.now(),
                })
                self._set_transaction_pending()
                return True
            else:
                error = tree['message']
                _logger.warn(error)
                self.sudo().write({
                    'state_message': error,
                    'acquirer_reference': tree["data"]["flw_ref"],
                    'date': fields.datetime.now(),
                })
                self._set_transaction_cancel()
                return False

    @api.model
    def _rave_form_get_tx_from_data(self, data):
        """ Given a data dict coming from flutterwave, verify it and find the related
        transaction record. """
        reference = data.get('reference')

        _logger.info("tx_ref before error:\n%s", pprint.pformat(reference))
        if not reference:
            flutterwave_error = data.get(
                'processor_response', {}).get('message', '')
            _logger.error('Flutterwave: invalid reply received from flutterwave API, looks like '
                          'the transaction failed. (error: %s)', flutterwave_error or 'n/a')
            error_msg = _(
                "We're sorry to report that the transaction has failed.")
            if flutterwave_error:
                error_msg += " " + (_("Flutterwave gave us the following info about the problem: '%s'") %
                                    flutterwave_error)
            error_msg += " " + _("Perhaps the problem can be solved by double-checking your "
                                 "credit card details, or contacting your bank?")
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx:
            error_msg = _(
                'Flutterwave: no order found for reference %s', reference)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        elif len(tx) > 1:
            error_msg = _('Flutterwave: %(count)s orders found for reference %(reference)s', count=len(
                tx), reference=reference)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx[0]
