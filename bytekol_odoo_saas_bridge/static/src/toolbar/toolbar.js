/**@odoo-module**/

import { isMobileOS } from '@web/core/browser/feature_detection';
import {renderToElement} from '@web/core/utils/render';
import {Component} from '@odoo/owl';
import {registry} from '@web/core/registry';
import {useService} from '@web/core/utils/hooks';
import {session} from '@web/session';
import {CustomAlertDialog} from "../dialogs/custom_alert_dialog";
import {_t} from "@web/core/l10n/translation";
import {markup} from "@odoo/owl";


export class StagingInfo extends Component {

    setup() {
        super.setup()
        this.dialog = useService('dialog');
        this.saas_client_data = session.odoo_saas_client_data;
        this.isMobile = isMobileOS();
    }

    _onClickStagingInfo() {
        const origin_odoo_entity_url = this.saas_client_data.staging_info.for_odoo_entity.url
        const body = _t(`
<div class="alert alert-info" role="alert">This is a staging database for: <a href="${origin_odoo_entity_url}" target="_blank">${origin_odoo_entity_url}</a>
You can use it to test some actions without affecting the real database like installing/uninstalling modules, ...

We have disabled Scheduled Actions and Email servers, you should also check and disable the 3rd party connection features to avoid affecting the real database.            
</div>
        `)
        this.dialog.add(CustomAlertDialog, {
            title: _t("Staging Info"),
            body: markup(body)
        })
    }

}

StagingInfo.template = 'bytekol_odoo_saas_bridge.staging_info_toolbar'
StagingInfo.props = {}

if (session['odoo_saas_client_data']?.staging_info?.is_staging) {
    registry
        .category("systray")
        .add("ActivationMenu", {Component: StagingInfo}, {sequence: 10000});
}
