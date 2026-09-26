import { apiRequest, ensureCsrfCookie } from "../../lib/api";
import type { LoginResult, MFAEnrollment, MFAStatus, Organisation, User } from "../../lib/types";

export async function fetchCurrentUser(): Promise<User> {
  return apiRequest<User>("/auth/me/");
}

export async function updateProfile(input: { first_name: string; last_name: string }): Promise<User> {
  return apiRequest<User>("/auth/me/", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export async function loginWithPassword(input: {
  email: string;
  password: string;
}): Promise<LoginResult> {
  await ensureCsrfCookie();
  return apiRequest<LoginResult>("/auth/session/", {
    method: "POST",
    body: JSON.stringify({
      email: input.email.trim().toLowerCase(),
      password: input.password,
    }),
  });
}

export async function signUp(input: {
  full_name: string;
  email: string;
  password: string;
  organisation_name: string;
}): Promise<{ user: User; organisation: Organisation }> {
  await ensureCsrfCookie();
  return apiRequest<{ user: User; organisation: Organisation }>("/auth/signup/", {
    method: "POST",
    body: JSON.stringify({
      full_name: input.full_name.trim(),
      email: input.email.trim().toLowerCase(),
      password: input.password,
      organisation_name: input.organisation_name.trim(),
    }),
  });
}

export async function verifyMfaCode(code: string): Promise<User> {
  return apiRequest<User>("/auth/mfa/verify/", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export async function getMfaStatus(): Promise<MFAStatus> {
  return apiRequest<MFAStatus>("/auth/mfa/status/");
}

export async function beginMfaEnrollment(): Promise<MFAEnrollment> {
  return apiRequest<MFAEnrollment>("/auth/mfa/enroll/begin/", { method: "POST", body: JSON.stringify({}) });
}

export async function confirmMfaEnrollment(code: string): Promise<{ backup_codes: string[] }> {
  return apiRequest<{ backup_codes: string[] }>("/auth/mfa/enroll/confirm/", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export async function disableMfa(password: string): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>("/auth/mfa/disable/", {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

export async function logoutSession(): Promise<void> {
  return apiRequest<void>("/auth/session/logout/", { method: "DELETE" });
}

export async function changePassword(input: {
  current_password: string;
  new_password: string;
}): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>("/auth/password/change/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function requestEmailChange(input: {
  new_email: string;
  current_password: string;
}): Promise<{ detail: string; development_verification_url?: string }> {
  return apiRequest<{ detail: string; development_verification_url?: string }>("/auth/email/change/", {
    method: "POST",
    body: JSON.stringify({
      new_email: input.new_email.trim().toLowerCase(),
      current_password: input.current_password,
    }),
  });
}

export async function confirmEmailChange(token: string): Promise<{ detail: string; email: string }> {
  await ensureCsrfCookie();
  return apiRequest<{ detail: string; email: string }>("/auth/email/change/confirm/", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export async function requestPasswordReset(input: { email: string }): Promise<{
  detail: string;
  development_reset_url?: string;
}> {
  await ensureCsrfCookie();
  return apiRequest<{ detail: string; development_reset_url?: string }>("/auth/password/reset/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function confirmPasswordReset(input: {
  uid: string;
  token: string;
  new_password: string;
}): Promise<{ detail: string }> {
  await ensureCsrfCookie();
  return apiRequest<{ detail: string }>("/auth/password/reset/confirm/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
