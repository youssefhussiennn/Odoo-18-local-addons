/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { _t } from "@web/core/l10n/translation";

export class VisitStartButton extends Component {
    static template = "atlas_operation_visits.VisitStartButton";
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ loading: false });
    }

    _getPosition() {
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 20000,
                maximumAge: 0,
            });
        });
    }

    _errorMessage(err) {
        switch (err && err.code) {
            case 1:
                return _t("Location permission denied. Allow location access in your browser and try again.");
            case 2:
                return _t("Location unavailable. Turn on GPS / location services and try again.");
            case 3:
                return _t("Getting the location timed out. Please try again.");
            default:
                return _t("Could not get your location.");
        }
    }

    async onClick() {
        if (!window.isSecureContext) {
            this.notification.add(
                _t("Location only works over HTTPS. Open Odoo with an https:// address and try again."),
                { type: "danger" }
            );
            return;
        }
        if (!navigator.geolocation) {
            this.notification.add(_t("This browser does not support location."), { type: "danger" });
            return;
        }
        this.state.loading = true;
        try {
            let position;
            try {
                position = await this._getPosition();
            } catch (err) {
                this.notification.add(this._errorMessage(err), { type: "danger" });
                return;
            }
            const record = this.props.record;
            const saved = await record.save();
            if (!saved) {
                return;
            }
            await this.orm.call("operation.visit", "action_start", [[record.resId]], {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy,
            });
            await record.model.load();
            this.notification.add(_t("Visit started and location captured."), { type: "success" });
        } finally {
            this.state.loading = false;
        }
    }
}

export const visitStartButton = {
    component: VisitStartButton,
};

registry.category("view_widgets").add("visit_start_button", visitStartButton);
