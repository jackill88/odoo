/** @odoo-module **/

import { normalize } from "@web/core/l10n/utils";

export function parseExtraBarcodeValues(value) {
    if (Array.isArray(value)) {
        return value
            .map((item) => (item ?? "").toString())
            .filter((item) => item);
    }

    if (typeof value === "string") {
        const trimmed = value.trim();
        if (!trimmed) {
            return [];
        }
        try {
            const parsed = JSON.parse(trimmed);
            if (Array.isArray(parsed)) {
                return parsed
                    .map((item) => (item ?? "").toString())
                    .filter((item) => item);
            }
        } catch (error) {
            // Fallthrough to treat the string literally.
        }
        return [trimmed];
    }

    if (value == null) {
        return [];
    }

    return [String(value)];
}

export function normalizedExtraBarcodeValues(value) {
    const parsed = parseExtraBarcodeValues(value);
    if (!parsed.length) {
        return "";
    }
    return normalize(parsed.join(" "));
}
