/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";

import { onWillStart, useState } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.access = useState({removeProperty: false});
        onWillStart(async() => {
            this.access.removeProperty = await this.orm.call(
                "access.management",
                "is_add_property_available",
                [1, this?.props?.resModel]
            );
        })
    },
    getStaticActionMenuItems() {
        const items = super.getStaticActionMenuItems(...arguments);
        if (this.access.removeProperty && items.addPropertyFieldValue) {
            delete items.addPropertyFieldValue;
        }
        return items;
    }
});