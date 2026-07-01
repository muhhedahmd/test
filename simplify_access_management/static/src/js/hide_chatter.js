/* @odoo-module */

import { FormRenderer } from "@web/views/form/form_renderer";
import { ListController } from "@web/views/list/list_controller";
import { FormController } from "@web/views/form/form_controller";
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
// NOTE: Odoo 19 fix — jsonrpc from "@web/core/network/rpc_service" was removed in Odoo 17.
// Import removed as it is unused — all RPC calls use this.orm service instead.
import { useService } from "@web/core/utils/hooks";

import { onMounted } from "@odoo/owl";

patch(FormRenderer.prototype, {
  setup() {
    super.setup();
    this.orm = useService("orm");
    
    onMounted(async () => {
      var hash = window.location.hash.replace("#", '').split("&");
      let cids;
      if(hash.findIndex(ele => ele.includes("cid")) == -1)
          cids = session.company_id;
      else {
          cids = hash.filter(ele => ele.includes("cid"))[0].split("=")[1].split(",");
          cids = cids.length > 0? parseInt(cids[0]): session.company_id;
      }
      let model = hash.filter(ele=>ele.includes("model"))?.[0];
      model = model? model.split("=")?.[1].split(",")?.[0]: model;
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
