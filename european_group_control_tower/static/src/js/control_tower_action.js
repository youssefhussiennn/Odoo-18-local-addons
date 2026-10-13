/** @odoo-module **/
import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";

/**
 * Hosts the Control Tower single page app (React 18, built with Vite into static/dist/egct.iife.js).
 *
 * The bundle is loaded lazily the first time the action is opened, so it never weighs on the regular
 * backend assets. The React app renders inside a Shadow DOM, which keeps its stylesheet fully isolated
 * from Odoo's Bootstrap styles (and vice versa). All data access goes through the `rpc` function passed
 * in below, i.e. through the logged-in user's Odoo session and access rights.
 */
export class ControlTowerAction extends Component {
    static template = "european_group_control_tower.ControlTowerAction";
    static props = ["*"];

    setup() {
        this.mountRef = useRef("mount");
        this.notification = useService("notification");
        this.state = useState({ loading: true });
        this.handle = null;
        this.destroyed = false;
        onMounted(() => this.start());
        onWillUnmount(() => this.stop());
    }

    async start() {
        try {
            const info = await rpc("/egct/info");
            await loadJS(info.bundleUrl);
            if (this.destroyed || !this.mountRef.el) {
                return;
            }
            this.handle = window.EGControlTower.mount(this.mountRef.el, {
                rpc: (route, params) => rpc(route, params || {}),
            });
        } catch (error) {
            this.notification.add(
                (error && error.message) || "The Control Tower could not be loaded.",
                { type: "danger", title: "Control Tower" }
            );
        } finally {
            this.state.loading = false;
        }
    }

    stop() {
        this.destroyed = true;
        if (this.handle) {
            this.handle.unmount();
            this.handle = null;
        }
    }
}

registry.category("actions").add("european_group_control_tower.control_tower", ControlTowerAction);
