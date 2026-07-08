"""Standalone tests for the menu-hide normalization algorithm.

This file does not import Odoo. It mirrors the normalization + hide logic
implemented in `models/ir_ui_menu.py` so we can test behavior on various
`load_menus()` shapes.
"""
from pprint import pprint


def apply_hide_to_res(res, hide_menu_ids):
    original_menus = res['menus']
    menus_was_list = False
    menus_by_id = {}

    if isinstance(original_menus, dict):
        for key, menu in original_menus.items():
            try:
                mid = int(key)
            except Exception:
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
                continue
            menus_by_id[mid] = dict(menu)
    else:
        return res

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

    to_hide = set()
    for m in hide_menu_ids:
        try:
            to_hide.add(int(m))
        except Exception:
            pass

    added = True
    while added:
        added = False
        for mid, menu in list(menus_by_id.items()):
            if mid in to_hide:
                continue
            p_id = _parent_id_as_int(menu.get('parent_id'))
            if p_id and p_id in to_hide:
                to_hide.add(mid)
                added = True

    for hid in list(to_hide):
        menus_by_id.pop(hid, None)

    for menu in menus_by_id.values():
        if 'children' in menu:
            menu['children'] = [c for c in _children_as_ints(menu.get('children')) if c not in to_hide]
        if 'child_id' in menu:
            menu['child_id'] = [c for c in _children_as_ints(menu.get('child_id')) if c not in to_hide]

    if menus_was_list:
        res['menus'] = [menu for menu in menus_by_id.values()]
    else:
        res['menus'] = {mid: menu for mid, menu in menus_by_id.items()}

    if 'root_menu_ids' in res:
        try:
            res['root_menu_ids'] = [int(r) for r in res.get('root_menu_ids') if int(r) not in to_hide]
        except Exception:
            pass

    return res


def test_case_dict_keys():
    res = {
        'menus': {
            1: {'id': 1, 'name': 'Dash', 'parent_id': None, 'children': [2, 3]},
            2: {'id': 2, 'name': 'Sales', 'parent_id': (1, 'Dash'), 'children': [4]},
            3: {'id': 3, 'name': 'Accounting', 'parent_id': (1, 'Dash'), 'children': []},
            4: {'id': 4, 'name': 'Orders', 'parent_id': (2, 'Sales'), 'children': []},
        },
        'root_menu_ids': [1]
    }
    out = apply_hide_to_res(res.copy(), [2])
    print('\nTest dict_keys hide [2]:')
    pprint(out)


def test_case_list_of_dicts():
    res = {
        'menus': [
            {'id': 1, 'name': 'Dash', 'parent_id': None, 'children': [2, 3]},
            {'id': 2, 'name': 'Sales', 'parent_id': 1, 'children': [4]},
            {'id': 3, 'name': 'Accounting', 'parent_id': 1, 'children': []},
            {'id': 4, 'name': 'Orders', 'parent_id': 2, 'children': []},
        ],
        'root_menu_ids': [1]
    }
    out = apply_hide_to_res(res.copy(), ["2"])  # string id
    print('\nTest list_of_dicts hide ["2"]:')
    pprint(out)


def test_case_string_keys():
    res = {
        'menus': {
            '1': {'id': '1', 'name': 'Dash', 'parent_id': None, 'children': ['2']},
            '2': {'id': '2', 'name': 'Sales', 'parent_id': ('1', 'Dash'), 'children': []},
        },
        'root_menu_ids': ['1']
    }
    out = apply_hide_to_res(res.copy(), [2])
    print('\nTest string_keys hide [2]:')
    pprint(out)


if __name__ == '__main__':
    test_case_dict_keys()
    test_case_list_of_dicts()
    test_case_string_keys()

