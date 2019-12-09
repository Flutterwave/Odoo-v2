# coding: utf-8

import logging
import requests
import pprint
import json

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)



class PaymentAcquirerRave(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('rave', 'Rave')])
    rave_public_key = fields.Char(required_if_provider='rave', groups='base.group_user')
    rave_secret_key = fields.Char(required_if_provider='rave', groups='base.group_user')
    environment = fields.Char(required_if_provider='rave', groups='base.group_user')

    @api.model
    def _get_rave_api_url(self):
        """ Rave URLs"""
        if self.environment == 'prod':
            return 'api.ravepay.co'
        else :
            return 'ravesandboxapi.flutterwave.com'

    def rave_form_generate_values(self, tx_values):
        self.ensure_one()
        rave_tx_values = dict(tx_values)
        temp_rave_tx_values = {
            'company': self.company_id.name,
            'amount': tx_values['amount'],  # Mandatory
            'currency': tx_values['currency'].name,  # Mandatory anyway
            'currency_id': tx_values['currency'].id,  # same here
            'address_line1': tx_values.get('partner_address'),  # Any info of the partner is not mandatory
            'address_city': tx_values.get('partner_city'),
            'address_country': tx_values.get('partner_country') and tx_values.get('partner_country').name or '',
            'email': tx_values.get('partner_email'),
            'address_zip': tx_values.get('partner_zip'),
            'name': tx_values.get('partner_name'),
            'phone': tx_values.get('partner_phone'),
        }

        rave_tx_values.update(temp_rave_tx_values)
        return rave_tx_values


class PaymentTransactionRave(models.Model):
    _inherit = 'payment.transaction'

    def _rave_verify_charge(self, data):
        api_url_charge = 'https://%s/flwv3-pug/getpaidx/api/v2/verify' % (self.acquirer_id._get_rave_api_url())
        payload = {
            'SECKEY': self.acquirer_id.rave_secret_key,
            'txref': self.reference,
        }
        headers = {
            'Content-Type': 'application/json',
        }
        
        _logger.info('_rave_verify_charge: Sending values to URL %s, values:\n%s', api_url_charge, pprint.pformat(payload))
        r = requests.post(api_url_charge,headers=headers, data=json.dumps(payload))
        # res = r.json()
        _logger.info('_rave_verify_charge: Values received:\n%s', pprint.pformat(r))
        return self._rave_validate_tree(r.json(),data)

    def _rave_validate_tree(self, tree, data):
        self.ensure_one()
        if self.state != 'draft':
            _logger.info('Rave: trying to validate an already validated tx (ref %s)', self.reference)
            return True

        status = tree.get('status')
        amount = tree["data"]["amount"]
        currency = tree["data"]["currency"]
        
        if status == 'success' and amount == data["amount"] and currency == data["currency"] :
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': tree["data"]["txid"],
            })
            self._set_transaction_done()
            self.execute_callback()
            if self.payment_token_id:
                self.payment_token_id.verified = True
            return True
        else:
            error = tree['message']
            _logger.warn(error)
            self.sudo().write({
                'state_message': error,
                'acquirer_reference':tree["data"]["txid"],
                'date': fields.datetime.now(),
            })
            self._set_transaction_cancel()
            return False