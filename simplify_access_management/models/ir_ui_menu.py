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
        # Be defensive: normalize different possible return shapes from Odoo core
        if not res or not isinstance(res, dict) or 'menus' not in res:
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

        # Normalize res['menus'] into a dict keyed by integer id so the algorithm
        # can work regardless of the exact shape returned by different Odoo versions.
        original_menus = res['menus']
        menus_was_list = False
        # Build a menu dict keyed by int id -> menu dict
        menus_by_id = {}

        if isinstance(original_menus, dict):
            for key, menu in original_menus.items():
                try:
                    mid = int(key)
                except Exception:
                    # fallback: try to extract id from menu itself
                    mid = int(menu.get('id')) if menu.get('id') else None
                if mid is None:
                    continue
                menus_by_id[mid] = dict(menu)
        elif isinstance(original_menus, (list, tuple)):
            menus_was_list = True
            for menu in original_menus:
                mid = None
                if isinstance(menu, dict) and menu.get('id'):
                    try:
                        mid = int(menu.get('id'))
                    except Exception:
                        mid = None
                if mid is None:
                    # ignore malformed entries
                    continue
                menus_by_id[mid] = dict(menu)
        else:
            # Unknown shape, give up safely
            return res

        # Helper to extract parent id as int or None
        def _parent_id_as_int(parent_val):
            if parent_val is None:
                return None
            if isinstance(parent_val, (list, tuple)) and parent_val:
                try:
                    return int(parent_val[0])
                except Exception:
                    return None
            try:
                return int(parent_val)
            except Exception:
                return None

        # Helper to normalize children list to ints
        def _children_as_ints(children_val):
            if not children_val:
                return []
            out = []
            for c in children_val:
                if isinstance(c, (list, tuple)) and c:
                    try:
                        out.append(int(c[0]))
                    except Exception:
                        continue
                else:
                    try:
                        out.append(int(c))
                    except Exception:
                        continue
            return out

        # Build initial to_hide set
        to_hide = set()
        for m in hide_menu_ids:
            try:
                mid = int(m)
            except Exception:
                continue
            to_hide.add(mid)

        # Recursively add descendants
        added = True
        while added:
            added = False
            for mid, menu in list(menus_by_id.items()):
                if mid in to_hide:
                    continue
                parent_raw = menu.get('parent_id')
                p_id = _parent_id_as_int(parent_raw)
                if p_id and p_id in to_hide:
                    to_hide.add(mid)
                    added = True

        # Remove hidden menus
        for hid in list(to_hide):
            if hid in menus_by_id:
                menus_by_id.pop(hid, None)

        # Filter children and child_id fields
        for menu in menus_by_id.values():
            if 'children' in menu:
                menu['children'] = [c for c in _children_as_ints(menu.get('children')) if c not in to_hide]
            if 'child_id' in menu:
                menu['child_id'] = [c for c in _children_as_ints(menu.get('child_id')) if c not in to_hide]

        # Filter root_menu_ids
        if 'root_menu_ids' in res:
            try:
                res['root_menu_ids'] = [int(r) for r in res.get('root_menu_ids') if int(r) not in to_hide]
            except Exception:
                # keep original if unexpected shape
                pass

        # Rebuild res['menus'] preserving original shape
        if menus_was_list:
            res['menus'] = [menu for menu in [dict(m) for m in menus_by_id.values()]]
        else:
            # key as int => some callers expect string keys; keep int keys
            res['menus'] = {mid: menu for mid, menu in menus_by_id.items()}

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

