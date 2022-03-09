# -*- coding: utf-8 -*-
import logging
import pprint

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from .const import EVENTS

_logger = logging.getLogger(__name__)

class RaveController(http.Controller):
    _return_url = "/payment/flutterwave/return"
    _notify_url = "/payment/flutterwave/notify"
    
    @http.route(
        _return_url, type='http', auth='public', methods=['GET','POST'], csrf=False,
        save_session=False
    )
    def rave_return(self, **data):
        """ Process the data returned by Flutterwave after redirection."""
        _logger.info("Received Flutterwave return data:\n%s", pprint.pformat(data))
        request.env['payment.transaction'].sudo()._handle_feedback_data('rave', data)
        return request.redirect('/payment/status')

    
    @http.route(_notify_url, type='http', auth='public', methods=['POST'], csrf=False)
    def rave_notify(self, **data):
        """ Process the data sent by Flutterwave to the webhook.
        :return: An empty string to acknowledge the notification
        :rtype: str
        """
        _logger.info("Received Flutterwave notify data:\n%s", pprint.pformat(data))
        try:
            request.env['payment.transaction'].sudo()._handle_feedback_data('rave', data)
        except ValidationError:  # Acknowledge the notification to avoid getting spammed
            _logger.exception("unable to handle the notification data; skipping to acknowledge")
        return ''  # Acknowledge the notification with an HTTP 200 response