/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";
import {registry} from "@web/core/registry";
const {xml} = owl;

export class OdooSaaSErrorDialog extends Dialog {
    setup() {
        super.setup();
        super.setup();
        this.title = this.env._t("Resource Limit Alert");
        const { data, message } = this.props;
        if (data && data.arguments && data.arguments.length > 0) {
            this.message = data.arguments[0];
        } else {
            this.message = message;
        }
    }
}

OdooSaaSErrorDialog.bodyTemplate = xml`<div class="alert alert-danger" style="font-size: 1.3rem" role="alert">
<t t-raw="message"/>
</div>`;

registry
    .category("error_dialogs")
    .add("odoo.addons.bytekol_odoo_saas_bridge.exceptions.OdooSaaSClientResourceException", OdooSaaSErrorDialog)
