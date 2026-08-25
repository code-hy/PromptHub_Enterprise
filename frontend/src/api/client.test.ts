import { describe, expect, it, vi } from "vitest";
import { api } from "./client";

// The client is a thin fetch wrapper; this test ensures it prefixes VITE_API_URL and throws on !ok.
describe("api client", () => {
  it("GET prefixes /api/v1 and parses JSON", async () => {
    const fake = { ok: true, status: 200, json: async () => ({ hello: "world" }) };
    (globalThis as unknown as { fetch: typeof fetch }).fetch = vi.fn().mockResolvedValue(fake as unknown as Response);
    const data = await api.get<{ hello: string }>("/catalog");
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/catalog"), expect.any(Object));
    expect(data.hello).toBe("world");
  });

  it("throws on non-ok", async () => {
    (globalThis as unknown as { fetch: typeof fetch }).fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: "Unprocessable Entity",
      text: async () => "validation error",
    } as unknown as Response);
    await expect(api.get("/prompts")).rejects.toThrow(/validation error/);
  });
});
