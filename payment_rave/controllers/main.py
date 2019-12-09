# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentProcessing

_logger = logging.getLogger(__name__)


class RaveController(http.Controller):
    
    @http.route(['/payment/values'], type='json', auth='public')
    def return_payment_values(self, **post):
        """ Upadate the payment values from the database"""
        acquirer_id = int(post.get('acquirer_id'))
        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        # values = acquirer.rave_form_generate_values(acquirer)
        return post

    @http.route(['/payment/rave/verify_charge'], type='json', auth='public')
    def rave_verify_charge(self, **post):
        """ Verify a payment transaction

        Expects the result from the user input from flwpbf-inline.js popup"""
        TX = request.env['payment.transaction']
        tx = None
        data = post.get('data');
        if post.get('tx_ref'):
            tx = TX.sudo().search([('reference', '=', post.get('tx_ref'))])
        if not tx:
            tx_id = (post.get('id') or request.session.get('sale_transaction_id') or
                     request.session.get('website_payment_tx_id'))
            tx = TX.sudo().browse(int(tx_id))
        if not tx:
            raise werkzeug.exceptions.NotFound()

        if tx.type == 'form_save' and tx.partner_id:
            payment_token_id = request.env['payment.token'].sudo().create({
                'acquirer_id': tx.acquirer_id.id,
                'partner_id': tx.partner_id.id,
            })
            tx.payment_token_id = payment_token_id
            response = tx._rave_verify_charge(data)
        else:
            response = tx._rave_verify_charge(data)
        _logger.info('Rave: entering form_feedback with post data %s', pprint.pformat(response))
        if response:
            request.env['payment.transaction'].sudo().with_context(lang=None).form_feedback(response, 'rave')
        # add the payment transaction into the session to let the page /payment/process to handle it
        PaymentProcessing.add_payment_transaction(tx)
        return "/payment/process"