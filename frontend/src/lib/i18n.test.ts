import { afterEach, describe, expect, it } from "vitest";

import { setLocale } from "./i18n";

afterEach(() => {
  setLocale("en");
});

describe("locale document metadata", () => {
  it("uses right-to-left direction for Arabic", () => {
    setLocale("ar");

    expect(document.documentElement).toHaveAttribute("lang", "ar");
    expect(document.documentElement).toHaveAttribute("dir", "rtl");
  });

  it("restores left-to-right direction for non-Arabic locales", () => {
    setLocale("ar");
    setLocale("fr");

    expect(document.documentElement).toHaveAttribute("lang", "fr");
    expect(document.documentElement).toHaveAttribute("dir", "ltr");
  });
});
