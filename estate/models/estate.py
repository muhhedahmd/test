# pyrefly: ignore [missing-import]
from odoo import models, fields, api

class Estate (models.Model):
    _name = 'estate'
    _description = 'Estate'

    name = fields.Char(required=True)
    last_seen = fields.Datetime(default=fields.Datetime.now)
    date = fields.Date(default=fields.Date.today)
    expected_price = fields.Float(required = True)
    best_price = fields.Float(readonly=True) 
    test= fields.Char(readonly= True) 
    active = fields.Boolean(default=True)
    Test1 = fields.Char() 
    Test2 = fields.Many2one('estate.type',string='Estate Type') 
    type_code = fields.Char(related='Test2.code', string='Type Code', readonly=True, store=True) 

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(Estate, self).fields_get(allfields, attributes=attributes)
        for field in res:
            res[field]['sortable'] = False
        return res 