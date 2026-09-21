import type { TroubleshootResponse } from "./types";

export async function troubleshoot(query: string, signal?: AbortSignal): Promise<TroubleshootResponse> {
  const response = await fetch("/v1/troubleshoot", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
    signal,
  });
  if (!response.ok) {
    throw new Error(`The engine returned an error (${response.status}).`);
  }
  return (await response.json()) as TroubleshootResponse;
}
