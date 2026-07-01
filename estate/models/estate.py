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
    # The relationship "circle":
    # 1. Estate (Property) points to Estate Type via Many2one 'Test2'.
    # 2. Estate Type points back to the list of Estates via One2many 'estateType'.
    Test2 = fields.Many2one('estate.type',string='Estate Type') 
    
    # In a related field:
    # - `related='Test2.code'` is the ONLY mandatory part to make it work.
    # - `readonly=True` is OPTIONAL (related fields are read-only by default).
    # - `store=True` is OPTIONAL (only needed to save in the database for index/sorting/filtering).
    # - `string='Type Code'` is OPTIONAL (defaults to the target field's label).
    type_code = fields.Char(related='Test2.code', string='Type Code', readonly=True, store=True) 

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(Estate, self).fields_get(allfields, attributes=attributes)
        for field in res:
            res[field]['sortable'] = False
        return res 