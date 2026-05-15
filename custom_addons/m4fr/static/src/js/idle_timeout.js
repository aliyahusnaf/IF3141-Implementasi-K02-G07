/** @odoo-module **/
import { registry } from "@web/core/registry";

const IDLE_TIMEOUT_MS = 30 * 60 * 1000; // 30 menit

registry.category("services").add("m4fr_idle_timeout", {
    start() {
        let timer = null;

        const logout = () => {
            window.location = "/web/session/logout?redirect=/web/login";
        };

        const resetTimer = () => {
            clearTimeout(timer);
            timer = setTimeout(logout, IDLE_TIMEOUT_MS);
        };

        const ACTIVITY_EVENTS = ["mousemove", "mousedown", "keydown", "scroll", "touchstart"];
        for (const event of ACTIVITY_EVENTS) {
            document.addEventListener(event, resetTimer, { passive: true, capture: true });
        }

        resetTimer();
    },
});
