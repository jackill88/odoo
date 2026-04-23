/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

async function digitalScalesUpload(env, action) {
    const params = action.params || {};
    const url = params.url;
    const headers = params.headers || {};
    const payload = params.payload || {};

    if (!url) {
        env.services.notification.add(
            _t("Digital scales sync failed"),
            { sticky: false, type: "danger" }
        );
        return;
    }

    try {
        const response = await fetch(url, {
            method: "POST",
            headers,
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            const errorText = await parseError(response);
            throw new Error(errorText);
        }
        const count = payload.items?.length || 0;
        env.services.notification.add(
            _t("Uploaded %(count)s weighted PLUs to the service.", { count }),
            { sticky: false, type: "success" }
        );
    } catch (error) {
        env.services.notification.add(
            error.message || _t("Unable to connect to the scales service."),
            { sticky: false, type: "danger" }
        );
    }
}

async function parseError(response) {
    try {
        const json = await response.json();
        return json.error || json.message || response.statusText || _t("Unknown error.");
    } catch (error) {
        return response.statusText || _t("Unknown error.");
    }
}

registry.category("actions").add("digital_scales_upload", digitalScalesUpload);
