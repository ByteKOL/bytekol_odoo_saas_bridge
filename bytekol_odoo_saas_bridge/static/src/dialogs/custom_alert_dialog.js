/** @odoo-module **/

import {AlertDialog} from "@web/core/confirmation_dialog/confirmation_dialog";

const {xml} = owl.tags;

export class CustomAlertDialog extends AlertDialog {
}

CustomAlertDialog.size = "modal-lg";
CustomAlertDialog.bodyTemplate = xml`
    <div class="text-prewrap" role="alert">
        <t t-raw="props.body"/>
    </div>`;
