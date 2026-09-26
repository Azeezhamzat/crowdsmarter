import { LANGUAGE_SELECTION_ENABLED, LOCALES, setLocale, useLocale } from "../lib/i18n";

export function LanguageSwitcher({ className = "" }: { className?: string }) {
  const locale = useLocale();
  if (!LANGUAGE_SELECTION_ENABLED) return null;

  return (
    <select
      className={`language-switcher ${className}`.trim()}
      value={locale}
      onChange={(event) => setLocale(event.target.value as typeof locale)}
      aria-label="Language"
    >
      {LOCALES.map((item) => (
        <option key={item.value} value={item.value}>{item.label}</option>
      ))}
    </select>
  );
}
