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

const IDEA_COMPETITION: Terminology = {
  ...GENERIC,
  decisionNoun: "Competition",
  decisionNounPlural: "Competitions",
  optionNoun: "Submission",
  optionNounPlural: "Submissions",
  addOptionCta: "Add a submission",
  committeeLabel: "Judging panel",
  roleLabels: {
    decision_owner: "Competition Organiser",
    decision_maker: "Head Judge",
    contributor: "Judge",
  },
  evidenceNoun: "Supporting material",
  ideaNoun: "Entry",
  ideaNounPlural: "Entries",
  submitIdeaCta: "Submit your entry",
  amountFieldLabel: "Prize requested",
};

const ANTICIPATORY_COMMONS: Terminology = {
  ...GENERIC,
  decisionNoun: "Commons decision",
  decisionNounPlural: "Commons decisions",
  optionNoun: "Response",
  optionNounPlural: "Responses",
  addOptionCta: "Add a possible response",
  committeeLabel: "Commons members",
  roleLabels: {
    decision_owner: "Commons Steward",
    decision_maker: "Accountable Member",
    contributor: "Member",
  },
  evidenceNoun: "Signal or observation",
  ideaNoun: "Signal",
  ideaNounPlural: "Signals",
  submitIdeaCta: "Share a signal",
  amountFieldLabel: "Resources needed",
};

const BY_TEMPLATE_KEY: Partial<Record<string, Terminology>> = {
  grant_round: GRANT_ROUND,
  idea_competition: IDEA_COMPETITION,
  anticipatory_commons: ANTICIPATORY_COMMONS,
};

export function getTerminology(templateKey?: string | null): Terminology {
  if (!templateKey) return GENERIC;
  return BY_TEMPLATE_KEY[templateKey] ?? GENERIC;
}
