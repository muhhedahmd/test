/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

import { onWillStart, useState } from "@odoo/owl";
const cogMenuRegistry = registry.category("cogMenu");

// NOTE: Odoo 19 fix — CogMenu was restructured in Odoo 18/19.
// Wrapped in try/catch so if the import or patch fails, it fails silently
// instead of crashing the entire JS bundle.
try {
patch(CogMenu.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.access = useState({removeSpreadsheet: false});
        onWillStart(async() => {
            if(this?.env?.config?.actionType == "ir.actions.act_window") {
                this.access.removeSpreadsheet = await this.orm.call(
                    "access.management",
                    "is_spread_sheet_available",
                    [1, this?.env?.config?.actionType, this?.env?.config?.actionId]
                );
                this.registryItems = await this._registryItems();
            }
        })
    },
    async _registryItems() {
        const items = [];
        for (const item of cogMenuRegistry.getAll()) {
            if(item?.Component?.name === "SpreadsheetCogMenu" && this.access.removeSpreadsheet)
                continue;
            if ("isDisplayed" in item ? await item.isDisplayed(this.env) : true) {
                items.push({
                    Component: item.Component,
                    groupNumber: item.groupNumber,
                    key: item.Component.name,
                });
            }
        }
        return items;
    }
})
} catch(e) {
    console.warn("[simplify_access_management] CogMenu patch skipped (component not found in this Odoo version):", e.message);
}