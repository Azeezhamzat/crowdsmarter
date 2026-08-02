import { downloadApiFile } from "../../lib/api";

export function downloadOrganisationExport(organisationId: string): Promise<string> {
  return downloadApiFile(`/organisations/${organisationId}/exports/complete/`);
}

export function downloadDecisionExport(decisionId: string): Promise<string> {
  return downloadApiFile(`/decisions/${decisionId}/export/`);
}
