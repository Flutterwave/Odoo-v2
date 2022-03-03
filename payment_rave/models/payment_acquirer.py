# coding: utf-8
import requests, json, logging
from tokenize import group
from werkzeug.urls import url_join

from .currencies import SUPPORTED_CURRENCIES

from odoo import api, fields, service, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    
    provider = fields.Selection(
        selection_add=[('rave', "Rave")], ondelete={'rave': 'cascade'})
    # provider = fields.Selection(selection_add=[('flutterwave', 'Flutterwave')], ondelete={'flutterwave': 'set default'})
    rave_public_key = fields.Char(required_if_provider='rave', groups='base.group_user')
    rave_secret_key = fields.Char(required_if_provider='rave', groups='base.group_user')
    rave_secret_hash = fields.Char(required_if_provider='rave', groups='base.group_user', string="Flutterwave Secret Hash")
    environment = fields.Char(required_if_provider='rave', groups='base.group_user')

    @api.model
    def _get_compatible_acquirers(self, *args, currency_id=None, **kwargs):
        """ Overide of payment to unlist Flutterwave acquirers if currency is not supported """
        acquirers = super()._get_compatible_acquirers(*args, currency_id=None, **kwargs)
        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name not in SUPPORTED_CURRENCIES:
            acquirers = acquirers.filtered(lambda a: a.provider != 'rave')
        return acquirers

    @api.model
    def _get_rave_api_url(self):
        self.ensure_one()
        """ Flutterwave URLs"""
        return 'https://api.flutterwave.com'

    def _flw_make_request(self, endpoint, payload=None, method='POST', offline=False):
        """  Make a request to Flutterwave API at the specified endpoint,
        
         Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict payload: The payload of the request
        :param str method: The HTTP method of the request
        :param bool offline: Whether the operation of the transaction being processed is 'offline'
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()

        url = 'https://api.flutterwave.com/v3' + endpoint

        odoo_version = service.common.exp_version()['server_version']
        module_version = self.env.ref('base.module_payment_rave').installed_version
        headers = {
            'Authorization': f'Bearer {self.rave_secret_key}',
            'Content-Type': 'application/json',
            "User-Agent": f'Odoo/{odoo_version} FlutterwaveNativeOdoo/{module_version}'
        }
        try:
            response = requests.request(method, url, data=json.dumps(payload), headers=headers, timeout=160)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            _logger.exception("Unable to communicate with Flutterwave: %s", url)
            raise ValidationError("Flutterwave: " + _("Could not establish the connection to the API."))
        return response.json()

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'rave':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_rave.payment_method_rave').id


    def _should_build_inline_form(self, is_validation=False):
        """ Return whether the inline form should be instantiated if it exists.
        For an acquirer to handle both direct payments and payment with redirection, it should
        override this method and return whether the inline form should be instantiated (i.e. if the
        payment should be direct) based on the operation (online payment or validation).
        :param bool is_validation: Whether the operation is a validation
        :return: Whether the inline form should be instantiated
        :rtype: bool
        """
        return False


