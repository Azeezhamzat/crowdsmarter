import { useSyncExternalStore } from "react";

/**
 * Minimal, dependency-free i18n: a typed per-page catalog plus a locale store
 * shared across the app via localStorage + useSyncExternalStore. French and
 * Portuguese strings are AI-assisted and have not been reviewed by a native
 * speaker - see docs/i18n.md.
 */
export type Locale = "en" | "fr" | "pt";

export const LOCALES: Array<{ value: Locale; label: string }> = [
  { value: "en", label: "English" },
  { value: "fr", label: "Français" },
  { value: "pt", label: "Português" },
];

const STORAGE_KEY = "crowdsmarter:locale";
const listeners = new Set<() => void>();

function isLocale(value: string | null): value is Locale {
  return value === "en" || value === "fr" || value === "pt";
}

function readStoredLocale(): Locale {
  if (typeof window === "undefined") return "en";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isLocale(stored) ? stored : "en";
}

let currentLocale: Locale = readStoredLocale();

export function getLocale(): Locale {
  return currentLocale;
}

export function setLocale(locale: Locale): void {
  currentLocale = locale;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, locale);
  }
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Returns the current locale and re-renders the calling component when it changes. */
export function useLocale(): Locale {
  return useSyncExternalStore(subscribe, getLocale, () => "en");
}

export type Catalog<T extends Record<string, string>> = Record<Locale, T>;

/** Preserves the exact key shape of the `en` catalog as the type for every locale. */
export function defineCatalog<T extends Record<string, string>>(catalog: {
  en: T;
  fr: T;
  pt: T;
}): Catalog<T> {
  return catalog;
}

/** Returns the strings object for the current locale, reactive to language changes. */
export function useTranslations<T extends Record<string, string>>(catalog: Catalog<T>): T {
  const locale = useLocale();
  return catalog[locale] ?? catalog.en;
}
