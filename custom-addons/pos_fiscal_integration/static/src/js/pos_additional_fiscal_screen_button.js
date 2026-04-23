import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import {FiscalIntegrationScreen} from "./pos_additional_fiscal_screen";
import { useService } from "@web/core/utils/hooks";
patch(ControlButtons.prototype, {
   setup() {
       super.setup();
       this.pos = usePos();
       this.dialog = useService("dialog");
   },
   onClick() {
       this.pos.navigate("FiscalIntegrationScreen");
   },
});
