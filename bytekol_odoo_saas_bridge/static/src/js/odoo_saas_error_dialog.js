/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";
import {registry} from "@web/core/registry";
import {_t} from "@web/core/l10n/translation";
import {standardErrorDialogProps} from "@web/core/errors/error_dialogs"
const {xml} = owl;
import { markup } from "@odoo/owl";


export class OdooSaaSErrorDialog extends Dialog {
    setup() {
        super.setup();
        this.title = _t("Resource Limit Alert");
        const { data, message } = this.props;
        if (data && data.arguments && data.arguments.length > 0) {
            this.message = markup(data.arguments[0]);
        } else {
            this.message = markup(message);
        }
    }
}

OdooSaaSErrorDialog.props = {
    ...standardErrorDialogProps,
}
// TODO: cannot use t-raw, inherit new template
OdooSaaSErrorDialog.template = xml`
    <t t-name="web.Dialog">
        <div class="o_dialog" t-att-id="id" t-att-class="{ o_inactive_modal: !data.isActive }">
            <div role="dialog" class="modal d-block"
                tabindex="-1"
                t-att-class="{ o_technical_modal: props.technical, o_modal_full: isFullscreen, o_inactive_modal: !data.isActive }"
                t-ref="modalRef"
                >
                <div class="modal-dialog modal-dialog-centered" t-attf-class="modal-{{props.size}}">
                    <div class="modal-content" t-att-class="props.contentClass" t-att-style="contentStyle">
                        <header t-if="props.header" class="modal-header">
                            <t t-slot="header" close="data.close" isFullscreen="isFullscreen">
                                <t t-call="web.Dialog.header">
                                    <t t-set="fullscreen" t-value="isFullscreen"/>
                                </t>
                            </t>
                        </header>
                        <!-- FIXME: WOWL there is a bug on t-portal on owl, in which t-portal don't work on multinode.
                        To avoid this we place the footer before the body -->
                        <footer t-if="props.footer" class="modal-footer justify-content-around justify-content-sm-start flex-wrap gap-1 w-100" style="order:2">
                            <t t-slot="footer" close="() => this.data.close()">
                                <button class="btn btn-primary o-default-button" t-on-click="() => this.data.close()">
                                    <t>Ok</t>
                                </button>
                            </t>
                        </footer>
                        <main class="modal-body" t-attf-class="{{ props.bodyClass }} {{ !props.withBodyPadding ? 'p-0': '' }}">
                            <div class="alert alert-danger" style="font-size: 1.3rem" role="alert">
                                <t t-out="message"/>
                            </div>
                        </main>
                    </div>
                </div>
            </div>
        </div>
    </t>

`
;

registry
    .category("error_dialogs")
    .add("odoo.addons.bytekol_odoo_saas_bridge.exceptions.OdooSaaSClientResourceException", OdooSaaSErrorDialog)
