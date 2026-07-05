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
            cids = int(cids)
        except Exception:
            cids = self.env.company.id
        
        access_management_obj = self.env['access.management'].sudo()
        access_management_rules = access_management_obj.search([
            ('user_ids', 'in', user.id),
            ('company_ids', 'in', cids),
            ('active', '=', True)
        ])
        hide_menus = access_management_rules.mapped('hide_menu_ids.menu_id')
        _logger.info("Access Management Search Debug - user: %s (ID %s), cids: %s, rules found: %s, hide_menus: %s",
                     user.name, user.id, cids, access_management_rules.mapped('name'), hide_menus)

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
        _logger.info("Access Management - load_menus method entered! self: %s, debug: %s", self, debug)
        res = super(ir_ui_menu, self).load_menus(debug)
        _logger.info("Access Management - load_menus res type: %s, keys: %s", type(res), list(res.keys()) if isinstance(res, dict) else 'Not a dict')
        
        if not res or not isinstance(res, dict):
            return res

        user = self.env.user
        try:
            cids = request.httprequest.cookies.get('cids') and request.httprequest.cookies.get('cids').split(',')[0] or self.env.company.id
            cids = int(cids)
        except Exception:
            cids = self.env.company.id

        access_management_obj = self.env['access.management'].sudo()
        access_management_rules = access_management_obj.search([
            ('user_ids', 'in', user.id),
            ('company_ids', 'in', cids),
            ('active', '=', True)
        ])
        hide_menu_ids = access_management_rules.mapped('hide_menu_ids.menu_id')

        _logger.info("Access Management Load Menus Debug - user: %s (ID %s), cids: %s, rules found: %s, hide_menus: %s",
                     user.name, user.id, cids, access_management_rules.mapped('name'), hide_menu_ids)

        if not hide_menu_ids:
            return res

        to_hide = set()
        for m in hide_menu_ids:
            to_hide.add(m)
            to_hide.add(str(m))

        res = dict(res)

        # Detect structure format: 
        # Format A (Odoo 16 and older): res has 'menus' key
        # Format B (Odoo 17/18/19): res itself contains the menu keys
        if 'menus' in res and isinstance(res['menus'], dict):
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

        else:
            # Format B (Odoo 17/18/19): res itself is the flat menus dictionary
            menu_keys = [k for k in res.keys() if k != 'root']
            for k in menu_keys:
                res[k] = dict(res[k])

            # Find all descendants of hidden menus recursively
            added = True
            while added:
                added = False
                for menu_id in menu_keys:
                    if menu_id not in to_hide and str(menu_id) not in to_hide:
                        menu = res[menu_id]
                        parent_id = menu.get('parent_id')
                        p_id = parent_id[0] if isinstance(parent_id, tuple) else parent_id
                        if p_id in to_hide or str(p_id) in to_hide:
                            to_hide.add(menu_id)
                            to_hide.add(str(menu_id))
                            added = True

            # Remove hidden menus from the tree
            res = {
                k: v for k, v in res.items()
                if k == 'root' or (k not in to_hide and str(k) not in to_hide)
            }

            # Filter the children lists in the remaining menus (including root)
            for k, menu in res.items():
                if 'children' in menu:
                    menu['children'] = [c for c in menu['children'] if c not in to_hide and str(c) not in to_hide]
                if 'child_id' in menu:
                    menu['child_id'] = [c for c in menu['child_id'] if c not in to_hide and str(c) not in to_hide]

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

