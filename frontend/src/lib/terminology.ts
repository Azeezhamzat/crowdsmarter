import type { ParticipantRole } from "./types";

export type Terminology = {
  decisionNoun: string;
  decisionNounPlural: string;
  optionNoun: string;
  optionNounPlural: string;
  addOptionCta: string;
  committeeLabel: string;
  roleLabels: Partial<Record<ParticipantRole, string>>;
  evidenceNoun: string;
  ideaNoun: string;
  ideaNounPlural: string;
  submitIdeaCta: string;
  amountFieldLabel: string;
};

const GENERIC: Terminology = {
  decisionNoun: "Decision",
  decisionNounPlural: "Decisions",
  optionNoun: "Option",
  optionNounPlural: "Options",
  addOptionCta: "Add an option",
  committeeLabel: "Participants",
  roleLabels: {},
  evidenceNoun: "Evidence",
  ideaNoun: "Idea",
  ideaNounPlural: "Ideas",
  submitIdeaCta: "Submit an idea",
  amountFieldLabel: "Estimated cost",
};

const GRANT_ROUND: Terminology = {
  ...GENERIC,
  decisionNoun: "Grant round",
  decisionNounPlural: "Grant rounds",
  optionNoun: "Application",
  optionNounPlural: "Applications",
  addOptionCta: "Add an application",
  committeeLabel: "Grant committee",
  roleLabels: {
    decision_owner: "Grant Program Lead",
    decision_maker: "Committee Chair",
    contributor: "Reviewer",
  },
  evidenceNoun: "Supporting document",
  ideaNoun: "Application",
  ideaNounPlural: "Applications",
  submitIdeaCta: "Submit an application",
  amountFieldLabel: "Requested amount",
};

const BY_TEMPLATE_KEY: Partial<Record<string, Terminology>> = {
  grant_round: GRANT_ROUND,
};

export function getTerminology(templateKey?: string | null): Terminology {
  if (!templateKey) return GENERIC;
  return BY_TEMPLATE_KEY[templateKey] ?? GENERIC;
}
