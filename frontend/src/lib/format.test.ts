import { describe, expect, it } from "vitest";
import { formatDate, formatTime, stripMarkdown, truncate } from "./format";

describe("format helpers", () => {
  it("formatTime returns empty for nullish", () => {
    expect(formatTime(null)).toBe("");
    expect(formatTime(undefined)).toBe("");
  });

  it("formatTime parses ISO", () => {
    expect(formatTime("2026-08-19T12:00:00Z")).toMatch(/2026/);
  });

  it("formatDate returns locale date", () => {
    expect(formatDate("2026-08-19T12:00:00Z")).toBeTruthy();
  });

  it("stripMarkdown removes fences and truncates", () => {
    const md = "## Hello\n```code``` **bold**";
    expect(stripMarkdown(md, 10)).toBe("Hello bold");
    expect(stripMarkdown("a".repeat(300), 220).length).toBe(221); // 220 + ellipsis
  });

  it("truncate shortens long strings", () => {
    expect(truncate("abcdef", 3)).toBe("abc…");
    expect(truncate("abc", 10)).toBe("abc");
  });
});
