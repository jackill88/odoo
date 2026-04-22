/** @odoo-module **/

const BARCODE_LENGTH = 13;
const PLU_LENGTH = 5;
const WEIGHT_LENGTH = 5;

/**
 * Try to parse a weighted goods barcode encoded as prefix + PLU + weight.
 * Returns null when the barcode does not look like a weighted code for the configured prefix.
 */
export function tryParseWeightedBarcode(rawCode, prefix) {
    if (prefix === null || prefix === undefined) {
        return null;
    }

    const digits = (rawCode || '').replace(/[^0-9]/g, '');
    if (digits.length !== BARCODE_LENGTH) {
        return null;
    }

    const prefixDigits = String(prefix).padStart(2, '0');
    if (!digits.startsWith(prefixDigits)) {
        return null;
    }

    const start = prefixDigits.length;
    const pluPart = digits.slice(start, start + PLU_LENGTH);
    const weightPart = digits.slice(start + PLU_LENGTH, start + PLU_LENGTH + WEIGHT_LENGTH);
    if (pluPart.length < PLU_LENGTH || weightPart.length < WEIGHT_LENGTH) {
        return null;
    }

    const plu = parseInt(pluPart, 10);
    const weight = parseInt(weightPart, 10);
    if (Number.isNaN(plu) || Number.isNaN(weight)) {
        return null;
    }

    return {
        type: 'weighted_goods',
        code: rawCode,
        base_code: `${prefixDigits}${pluPart}${'0'.repeat(WEIGHT_LENGTH)}`,
        plu,
        weight,
        value: weight,
    };
}
