/** @odoo-module **/

import { registry } from "@web/core/registry";

// Alias terabits_domain to the native Odoo 19 domain widget
// so that widget="terabits_domain" in views renders correctly
// without requiring advanced_web_domain_widget as a dependency.
const domainField = registry.category("fields").get("domain");
if (domainField) {
    registry.category("fields").add("terabits_domain", domainField);
}
