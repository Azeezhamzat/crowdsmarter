/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_PUBLIC_CONTACT_EMAIL?: string;
  readonly VITE_DEMO_EMAIL?: string;
  readonly VITE_SUPPORT_EMAIL?: string;
  readonly VITE_PRIVACY_EMAIL?: string;
  readonly VITE_SECURITY_EMAIL?: string;
  readonly VITE_ADMIN_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
