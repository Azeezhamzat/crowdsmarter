import type { ForesightSignal } from "../../lib/types";

export const steepDotColour: Record<ForesightSignal["steep_category"], string> = {
  social: "#7f5fd9",
  technological: "#1f8fc4",
  economic: "#c9962a",
  environmental: "#2f8a5b",
  political: "#c1553f",
  legal: "#5b6478",
  ethical: "#b1489a",
};
