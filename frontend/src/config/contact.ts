type RuntimeEnvironment = Record<string, string | undefined>;

type PublicContactConfiguration = {
  public_contact_email: string;
  demo_email: string;
  support_email: string;
  privacy_email: string;
  security_email: string;
};

const runtimeEnvironment = import.meta.env as unknown as RuntimeEnvironment;

function configuredEmail(key: string, fallback: string): string {
  const value = runtimeEnvironment[key]?.trim();
  return value || fallback;
}

function configuredUrl(key: string, fallback: string): string {
  const value = runtimeEnvironment[key]?.trim();
  return value || fallback;
}

export const contactChannels: {
  general: string;
  demo: string;
  support: string;
  privacy: string;
  security: string;
  adminUrl: string;
} = {
  general: configuredEmail("VITE_PUBLIC_CONTACT_EMAIL", "hello@crowdsmarter.com"),
  demo: configuredEmail("VITE_DEMO_EMAIL", "hello@crowdsmarter.com"),
  support: configuredEmail("VITE_SUPPORT_EMAIL", "hello@crowdsmarter.com"),
  privacy: configuredEmail("VITE_PRIVACY_EMAIL", "hello@crowdsmarter.com"),
  security: configuredEmail("VITE_SECURITY_EMAIL", "hello@crowdsmarter.com"),
  adminUrl: configuredUrl("VITE_ADMIN_BASE_URL", "http://localhost:8000/admin/"),
};

export async function loadPublicContactChannels(): Promise<void> {
  const apiBaseUrl = configuredUrl("VITE_API_BASE_URL", "/api/v1").replace(/\/$/, "");
  try {
    const response = await fetch(`${apiBaseUrl}/public/configuration/`, {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    });
    if (!response.ok) return;
    const payload = await response.json() as PublicContactConfiguration;
    contactChannels.general = payload.public_contact_email || contactChannels.general;
    contactChannels.demo = payload.demo_email || contactChannels.demo;
    contactChannels.support = payload.support_email || contactChannels.support;
    contactChannels.privacy = payload.privacy_email || contactChannels.privacy;
    contactChannels.security = payload.security_email || contactChannels.security;
  } catch {
    // Environment defaults keep the public site usable during backend startup or recovery.
  }
}

export function buildMailto(
  email: string,
  subject: string,
  body?: string,
): string {
  const parameters = new URLSearchParams({ subject });
  if (body) parameters.set("body", body);
  return `mailto:${email}?${parameters.toString()}`;
}
