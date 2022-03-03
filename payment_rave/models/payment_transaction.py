import logging
import requests
import pprint
import json

from werkzeug.urls import url_join, url_encode

from odoo import _, api, models, fields
from odoo.exceptions import ValidationError
from odoo.addons.payment_rave.controllers.main import RaveController
# from odoo.addons.payment.payment_rave.controllers.main import RaveController

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Flutterwave-specific rendering values.
        Note: self.ensure_one() from `_get_processing_values`
        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'rave':
            return res

        payload = self._flutterwave_prepare_payment_request_payload()
        _logger.info("sending '/payments' request for link creation:\n%s", pprint.pformat(payload))
        payment_data = self.acquirer_id._flw_make_request('/payments', payload=payload)

        # The acquirer reference is set now to allow fetching the payment status after redirection
        self.acquirer_reference = self.reference

        if payment_data.get('status') != 'success':
            return 'Hey there'
        return {'api_url': payment_data.get('data').get('link')}

    def _flutterwave_prepare_payment_request_payload(self):
        """ Create the payload for the payment request based on the transaction values.
        :return: The request payload
        :rtype: dict
        """
        base_url = self.acquirer_id.get_base_url()
        return_url = RaveController._return_url

        return {
            'tx_ref': self.reference,
            'amount': f"{self.amount:.2f}",
            'currency': self.currency_id.name,
            'redirect_url': f'{url_join(base_url, return_url)}',
            'customer': {
                'email': self.partner_email,
                'phone_number': self.partner_phone,
                'name' : self.partner_name
            }
        }

    def _get_tx_from_feedback_data(self, provider, data):
        """ Override of payment to find the transaction based on Flutterwave data.
        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'rave':
            return tx
        
        reference = data.get('tx_ref')
        transaction_id = data.get('transaction_id')
        from_flutterwave_status = data.get('status')

        if not reference:
            raise ValidationError("Flutterwave: " + _("Received data with missing merchant reference"))

        tx = self.search([('reference', '=', reference ), ('provider', '=', 'rave')])
        if not tx:
            raise ValidationError(
                "Flutterwave: " + _("No transaction found matching reference %s.", reference )
            )
        return tx

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on Flutterwave data.
        Note: self.ensure_one()
        :param dict data: The feedback data sent by the provider
        :return: None
        """
        super()._process_feedback_data(data)
        if self.provider != 'rave':
            return

        if 'tx_ref' in data:
            self.acquirer_reference = data.get('data').get('tx_ref')

        payment_data = self.acquirer_id._flw_make_request(
            f'/transactions/verify_by_reference?tx_ref={self.acquirer_reference}', payload=None, method="GET"
        )
        payment_status = payment_data.get('data').get('status') #confirm this is correct

        if payment_status == 'successful':
            self._set_done()
        elif payment_status in ['cancelled', 'failed']:
            self._set_canceled("Flutterwave: " + _("Canceled payment with status: %s", payment_status))
        else:
            _logger.info("Received data with invalid payment status: %s", payment_status)
            self._set_error(
                "Flutterwave: " + _("Received data with invalid payment status: %s", payment_status)
            )
