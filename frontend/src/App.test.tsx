import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const plan = {
  query: "touch is laggy",
  query_variations: ["a", "b", "c", "d", "e", "f", "g", "h"],
  response: {
    contexts: [{
      goal: "Follow these steps to perform this Touchscreen Issues Troubleshooting",
      title: "Touchscreen issues",
      score: 0.9,
      actions: [{
        actionName: "Touch Sensitivity Setting",
        description: "It will help with touch sensitivity setting",
        category: "auto",
        stepGroups: [{
          steps: ["Go to Settings.", "Tap Display."],
          actionableDeeplink: { deeplink: "bixby://masked/act/14eb42b895", description: "d", message: "Enable Touch sensitivity", originalType: "onURL" },
          validationDeeplink: { deeplink: "bixby://masked/val/6451858b28", key: "Touch sensitivity" },
        }],
      }],
    }],
  },
  meta: { latency_ms: 12, cache_hit: true, model: "rules-v1", cost_usd: 0 },
};

function mockFetch(body: unknown, ok = true) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok, status: ok ? 200 : 500, json: async () => body }));
}

beforeEach(() => mockFetch(plan));
afterEach(() => vi.unstubAllGlobals());

async function send(text: string) {
  await userEvent.type(screen.getByLabelText("Describe your problem"), text);
  await userEvent.click(screen.getByRole("button", { name: "Send" }));
}

describe("App", () => {
  it("sends the message, renders the plan and its meta strip", async () => {
    render(<App />);
    await send("touch is laggy");
    expect(await screen.findByText(plan.response.contexts[0].goal)).toBeInTheDocument();
    expect(screen.getByText(/12 ms/)).toBeInTheDocument();
    expect(screen.getByText(/cache hit/)).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/v1/troubleshoot", expect.objectContaining({ method: "POST" }));
  });

  it("drives the phone simulator from the Open button", async () => {
    render(<App />);
    await send("touch is laggy");
    await userEvent.click(await screen.findByRole("button", { name: "Open Enable Touch sensitivity" }));
    const phone = screen.getByLabelText("Phone simulator");
    expect(within(phone).getByText("Touch sensitivity")).toBeInTheDocument();
    expect(within(phone).getByText("Turned on")).toBeInTheDocument();
    expect(within(phone).getByText(/Verified: Touch sensitivity/)).toBeInTheDocument();
  });

  it("explains an empty result", async () => {
    mockFetch({ ...plan, response: { contexts: [] }, meta: { ...plan.meta, fallback: "no_match", cache_hit: false } });
    render(<App />);
    await send("best pasta recipe");
    expect(await screen.findByText(/couldn't find a verified fix/i)).toBeInTheDocument();
  });

  it("shows a friendly error when the engine is unreachable", async () => {
    mockFetch({}, false);
    render(<App />);
    await send("touch is laggy");
    expect(await screen.findByRole("alert")).toHaveTextContent(/engine/i);
  });
});
