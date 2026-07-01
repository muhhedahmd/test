/** @odoo-module **/

import { registry } from "@web/core/registry";

const domainField = registry.category("fields").get("domain");
if (domainField) {
    registry.category("fields").add("terabits_domain", domainField);
}
