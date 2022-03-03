import logging
import pprint

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentToken(models.Model):
    _inherit = 'payment.token'

    rave_payment_method = fields.Char('Rave Payment Method')