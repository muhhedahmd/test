from odoo import models

class Estate (models.Model):
    _name = 'estate'
    _description = 'Estate'

    name =  fields.Char(required = True)
    date = fields.Date(default=fields.Datetime.now())
    expected_price = fields.Float(required = True)
    best_price = fields.Float(readonly=True)
    

