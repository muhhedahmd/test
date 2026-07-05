from odoo import fields, models, api, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class ir_ui_menu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        ids = super(ir_ui_menu, self).search(args, offset=0, limit=None, order=order)
        user = self.env.user
        try:
            cids = request.httprequest.cookies.get('cids') and request.httprequest.cookies.get('cids').split(',')[0] or self.env.company.id
        except Exception:
            cids = self.env.company.id
        
        hide_menus = user.access_management_ids.filtered(lambda line: int(cids) in line.company_ids.ids).mapped('hide_menu_ids.menu_id')
        _logger.info("Access Management Search Debug - user: %s (ID %s), cids: %s, rules: %s, hide_menus: %s",
                     user.name, user.id, cids, [(r.name, r.active, r.company_ids.ids) for r in user.access_management_ids], hide_menus)

        for menu_id in hide_menus:
            menu_id = self.browse(menu_id)
            if menu_id in ids:
                ids = ids - menu_id
        if offset:
            ids = ids[offset:]
        if limit:
            ids = ids[:limit]
        return ids

    @api.model
    def load_menus(self, debug=False):
        res = super(ir_ui_menu, self).load_menus(debug)
        if not res or not isinstance(res, dict) or 'menus' not in res:
            return res

        user = self.env.user
        try:
            cids = request.httprequest.cookies.get('cids') and request.httprequest.cookies.get('cids').split(',')[0] or self.env.company.id
        except Exception:
            cids = self.env.company.id

        hide_menu_ids = user.access_management_ids.filtered(
            lambda line: int(cids) in line.company_ids.ids
        ).mapped('hide_menu_ids.menu_id')

        _logger.info("Access Management Load Menus Debug - user: %s (ID %s), cids: %s, rules: %s, hide_menus: %s",
                     user.name, user.id, cids, [(r.name, r.active, r.company_ids.ids) for r in user.access_management_ids], hide_menu_ids)

        if not hide_menu_ids:
            return res

        # Convert hide_menu_ids to set of both int and str to handle any key representation safely
        to_hide = set()
        for m in hide_menu_ids:
            to_hide.add(m)
            to_hide.add(str(m))

        # Copy the dictionaries to avoid mutating Odoo's cached menu tree
        res = dict(res)
        res['menus'] = {menu_id: dict(menu) for menu_id, menu in res['menus'].items()}
        if 'root_menu_ids' in res:
            res['root_menu_ids'] = list(res['root_menu_ids'])

        # Find all descendants of hidden menus recursively
        added = True
        while added:
            added = False
            for menu_id, menu in res['menus'].items():
                if menu_id not in to_hide:
                    parent_id = menu.get('parent_id')
                    p_id = parent_id[0] if isinstance(parent_id, tuple) else parent_id
                    if p_id in to_hide or str(p_id) in to_hide:
                        to_hide.add(menu_id)
                        to_hide.add(str(menu_id))
                        added = True

        # Remove hidden menus from the tree
        res['menus'] = {
            menu_id: menu
            for menu_id, menu in res['menus'].items()
            if menu_id not in to_hide
        }

        if 'root_menu_ids' in res:
            res['root_menu_ids'] = [r for r in res['root_menu_ids'] if r not in to_hide]

        # Filter the children lists in the remaining menus
        for menu in res['menus'].values():
            if 'children' in menu:
                menu['children'] = [c for c in menu['children'] if c not in to_hide]
            if 'child_id' in menu:
                menu['child_id'] = [c for c in menu['child_id'] if c not in to_hide]

        return res
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(ir_ui_menu, self).create(vals_list)
        menu_item_obj = self.env['menu.item']
        for record in res:
            menu_item_obj.create({'name':record.display_name,'menu_id':record.id})
        return res

    def unlink(self):
        menu_item_obj = self.env['menu.item']
        for record in self:
            menu_item_obj.search([('menu_id','=',record.id)]).unlink()
        return super(ir_ui_menu, self).unlink()

