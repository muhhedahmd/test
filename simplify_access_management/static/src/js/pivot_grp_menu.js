/** @odoo-module **/
import { PivotGroupByMenu } from "@web/views/pivot/pivot_group_by_menu";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, useState } from "@odoo/owl";

// NOTE: Odoo 19 fix — PivotGroupByMenu was restructured/removed in Odoo 18/19.
// Wrapped in try/catch so if the component doesn't exist, it fails silently.
try {
patch(PivotGroupByMenu.prototype, {
  setup() {
    super.setup(...arguments);
    this.orm = useService("orm");
    onWillStart(async () => {
      const res = await this.orm.call("access.management", "get_hidden_field", [
        "",
        this?.env?.searchModel?.resModel,
      ]);
      this.fields = this.fields.filter((ele) => !res.includes(ele.name));
    });
  },
});
} catch(e) {
    console.warn("[simplify_access_management] PivotGroupByMenu patch skipped:", e.message);
}
