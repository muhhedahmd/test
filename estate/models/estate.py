from odoo import models, fields

class Estate (models.Model):
    _name = 'estate'
    _description = 'Estate'

    name =  fields.Char(required = True)
    date = fields.Date(default=fields.Date.today)
    expected_price = fields.Float(required = True)
    best_price = fields.Float(readonly=True) 
    test= fields.Char(readonly= True) 
