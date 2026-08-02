import { apiRequest, ensureCsrfCookie } from "../../lib/api";
import type { User } from "../../lib/types";

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
}): Promise<User> {
  await ensureCsrfCookie();
  return apiRequest<User>("/auth/session/", {
    method: "POST",
    body: JSON.stringify({
      email: input.email.trim().toLowerCase(),
      password: input.password,
    }),
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
