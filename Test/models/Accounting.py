from odoo import models , fields
class Accounting(models.Model):
    _inherit = "account.move"
    name_testttst = fields.char(string="Name")

