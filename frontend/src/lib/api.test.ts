import { afterEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "./api";
import { setLocale } from "./i18n";

afterEach(() => {
  vi.restoreAllMocks();
  setLocale("en");
  document.cookie = "csrftoken=; Max-Age=0; path=/";
});

describe("apiRequest", () => {
  it("sends credentials and the CSRF token on mutations", async () => {
    document.cookie = "csrftoken=test-token; path=/";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    await apiRequest<{ ok: boolean }>("/example/", {
      method: "POST",
      body: JSON.stringify({ name: "Acme" }),
    });

    expect(fetchMock).toHaveBeenCalledOnce();
    const [, init] = fetchMock.mock.calls[0] ?? [];
    const headers = new Headers(init?.headers);
    expect(init?.credentials).toBe("include");
    expect(headers.get("X-CSRFToken")).toBe("test-token");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("sends the selected locale so backend messages use the same language", async () => {
    setLocale("ar");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    await apiRequest<{ ok: boolean }>("/example/");

    const [, init] = fetchMock.mock.calls[0] ?? [];
    const headers = new Headers(init?.headers);
    expect(headers.get("Accept-Language")).toBe("ar");
  });

  it("surfaces field-level domain validation messages", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ participants: ["Add at least one stakeholder."] }), {
        status: 400,
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(apiRequest("/example/")).rejects.toThrow(
      "Add at least one stakeholder.",
    );
  });
});
