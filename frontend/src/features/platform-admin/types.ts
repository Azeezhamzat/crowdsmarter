import type { User } from "../../lib/types";

export type PlatformCounts = {
  users: number;
  active_users: number;
  platform_administrators: number;
  organisations: number;
  active_organisations: number;
  deactivated_organisations: number;
  active_decisions: number;
  pending_invitations: number;
  new_demo_requests: number;
  active_support_access: number;
};

export type PlatformAuditEvent = {
  id: string;
  action: string;
  object_type: string;
  object_id: string;
  actor: User | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type PlatformDemoRequest = {
  id: string;
  full_name: string;
  work_email: string;
  organisation_name: string;
  job_title: string;
  organisation_size: string;
  organisation_size_label: string;
  primary_need: string;
  primary_need_label: string;
  message: string;
  status: "new" | "contacted" | "qualified" | "closed";
  created_at: string;
  updated_at: string;
};

export type SupportAccessGrant = {
  id: string;
  administrator: User;
  organisation: string;
  organisation_name: string;
  access_level: "read_only" | "operational";
  reason: string;
  status: "active" | "revoked" | "expired";
  expires_at: string;
  revoked_by: User | null;
  revoked_at: string | null;
  is_current: boolean;
  created_at: string;
  updated_at: string;
};

export type PlatformOverview = {
  counts: PlatformCounts;
  recent_audit_events: PlatformAuditEvent[];
  recent_demo_requests: PlatformDemoRequest[];
  active_support_access: SupportAccessGrant[];
};

export type PlatformOwner = {
  membership_id: string;
  user_id: string;
  email: string;
  name: string;
};

export type PlatformOrganisation = {
  id: string;
  name: string;
  slug: string;
  description: string;
  brand_name: string;
  website_url: string;
  primary_colour: string;
  status: "active" | "deactivated";
  retention_days: number | null;
  created_at: string;
  updated_at: string;
  member_count: number;
  active_owner_count: number;
  workspace_count: number;
  decision_count: number;
  active_decision_count: number;
  pending_invitation_count: number;
  owners: PlatformOwner[];
};

export type PlatformMembership = {
  id: string;
  user: User;
  role: "owner" | "admin" | "contributor" | "viewer";
  status: "active" | "suspended";
  created_at: string;
  updated_at: string;
};

export type PlatformInvitation = {
  id: string;
  email: string;
  role: "owner" | "admin" | "contributor" | "viewer";
  status: "pending" | "accepted" | "revoked";
  effective_status: "pending" | "accepted" | "revoked" | "expired";
  invited_by: User;
  expires_at: string;
  last_sent_at: string | null;
  send_count: number;
  created_at: string;
};

export type PlatformOrganisationDetail = PlatformOrganisation & {
  memberships: PlatformMembership[];
  invitations: PlatformInvitation[];
  workspaces: Array<{
    id: string;
    name: string;
    slug: string;
    is_default: boolean;
    decision_count: number;
  }>;
  decisions: Array<{
    id: string;
    title: string;
    status: string;
    urgency: string;
    owner: { id: string; email: string; name: string };
    updated_at: string;
  }>;
  current_support_access: SupportAccessGrant | null;
};

export type PlatformUser = User & {
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  is_platform_administrator: boolean;
  organisation_count: number;
  active_owned_organisation_count: number;
  date_joined: string;
  last_login: string | null;
};

export type AIProviderKey = "rules" | "anthropic" | "openai" | "gemini";

export type PlatformContactSettings = {
  public_contact_email: string;
  demo_email: string;
  support_email: string;
  privacy_email: string;
  security_email: string;
  notification_sender_email: string;
  support_access_max_hours: number;
};

export type PlatformConfiguration = PlatformContactSettings & {
  ai_provider_key: AIProviderKey;
  ai_provider_key_label: string;
  ai_provider_model: string;
  ai_provider_api_key_is_set: boolean;
  updated_at: string;
};

export type AIProviderConnectionResult = {
  ok: boolean;
  detail: string;
  provider_key: string;
  provider_label: string;
};

export type PlatformAdministrator = {
  id: string;
  user: User;
  status: "active" | "suspended";
  rationale: string;
  granted_by: User | null;
  suspended_by: User | null;
  suspended_at: string | null;
  created_at: string;
  updated_at: string;
};
