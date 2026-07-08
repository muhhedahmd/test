/* @odoo-module */

import { FormRenderer } from "@web/views/form/form_renderer";
// NOTE: Odoo 19 fix — ListController and FormController imports were unused. Removed.
// NOTE: Odoo 19 fix — jsonrpc from "@web/core/network/rpc_service" was removed in Odoo 17. Removed.
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

patch(FormRenderer.prototype, {
  setup() {
    super.setup();
    this.orm = useService("orm");

    onMounted(async () => {
      // NOTE: Odoo 19 fix — window.location.hash was used in Odoo 16/17 (hash-based routing).
      // Odoo 18/19 uses path-based URLs (/odoo/model-name).
      // Now reading cids from cookie and model from this.props.record directly.
      let cids = session.company_id;
      try {
        const cookieCids = document.cookie.split(';').find(c => c.trim().startsWith('cids='));
        if (cookieCids) {
          cids = parseInt(cookieCids.split('=')[1].split(',')[0]);
        }
      } catch(e) {}

      let model;
      try {
        model = this.props?.record?.resModel || this.env?.model?._config?.resModel;
      } catch(e) {}

      if (cids && model) {
        const result = await this.orm.call("access.management", "get_chatter_hide_details", [
          session.user_id,
          cids,
          model,
        ]);
        if (!result["hide_send_mail"]) {
          var btn1 = setInterval(function () {
            if ($(".o-mail-Chatter-sendMessage").length) {
              $(".o-mail-Chatter-sendMessage").remove();
              clearInterval(btn1);
            }
          }, 50);
        }
        if (!result["hide_log_notes"]) {
          var btn2 = setInterval(function () {
            if ($(".o-mail-Chatter-logNote").length) {
              $(".o-mail-Chatter-logNote").remove();
              clearInterval(btn2);
            }
          }, 50);
        }
        if (!result["hide_schedule_activity"]) {
          var btn3 = setInterval(function () {
            if ($(".o-mail-Chatter-activity").length) {
              $(".o-mail-Chatter-activity").remove();
              clearInterval(btn3);
            }
          }, 50);
        }
      }
    });
  },
});
