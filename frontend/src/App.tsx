import { FormEvent, useEffect, useRef, useState } from "react";
import { troubleshoot } from "./api";
import { PhoneSimulator } from "./PhoneSimulator";
import { PlanCard } from "./PlanCard";
import { openDeeplink, type SimScreen } from "./simulator";
import type { TroubleshootResponse } from "./types";

type Message =
  | { id: number; role: "user"; text: string }
  | { id: number; role: "bot"; data: TroubleshootResponse }
  | { id: number; role: "error"; text: string };

const EXAMPLES = [
  "My screen is cracked and flickers",
  "Touch responses are laggy",
  "Screen stays black when I turn it on",
];

function MetaStrip({ data }: { data: TroubleshootResponse }) {
  const { latency_ms, cache_hit, model, cost_usd } = data.meta;
  return (
    <p className="meta">
      {latency_ms} ms · {cache_hit ? "cache hit" : "cache miss"} · {model} · ${cost_usd.toFixed(2)}
    </p>
  );
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [screen, setScreen] = useState<SimScreen | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const nextId = useRef(1);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  async function send(text: string) {
    const query = text.trim();
    if (!query || busy) return;
    setDraft("");
    setBusy(true);
    setMessages((current) => [...current, { id: nextId.current++, role: "user", text: query }]);
    try {
      const data = await troubleshoot(query);
      setMessages((current) => [...current, { id: nextId.current++, role: "bot", data }]);
    } catch (error) {
      const text = error instanceof Error ? error.message : "The engine could not be reached.";
      setMessages((current) => [...current, { id: nextId.current++, role: "error", text }]);
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void send(draft);
  }

  return (
    <div className="app">
      <main className="chat">
        <header className="chat__head">
          <h1>Galaxy Troubleshooter</h1>
          <p>Describe what's wrong in your own words. You'll get an ordered plan you can open step by step.</p>
        </header>

        <div className="thread" aria-live="polite">
          {messages.length === 0 && (
            <div className="examples">
              {EXAMPLES.map((example) => (
                <button key={example} type="button" className="chip" onClick={() => void send(example)}>
                  {example}
                </button>
              ))}
            </div>
          )}
          {messages.map((message) => {
            if (message.role === "user") return <p key={message.id} className="bubble bubble--user">{message.text}</p>;
            if (message.role === "error") return <p key={message.id} role="alert" className="bubble bubble--error">{message.text}</p>;
            const contexts = message.data.response.contexts;
            return (
              <div key={message.id} className="bubble bubble--bot">
                {contexts.length === 0 ? (
                  <p>I couldn't find a verified fix for that. Try describing the symptom or the screen you're on.</p>
                ) : (
                  contexts.map((goal) => (
                    <PlanCard
                      key={goal.goal}
                      goal={goal}
                      activeUri={screen?.uri ?? null}
                      onOpen={(link, validation) => setScreen(openDeeplink(link, validation))}
                    />
                  ))
                )}
                <MetaStrip data={message.data} />
              </div>
            );
          })}
          {busy && <p className="bubble bubble--bot bubble--pending">Working on it…</p>}
          <div ref={endRef} />
        </div>

        <form className="composer" onSubmit={onSubmit}>
          <input
            aria-label="Describe your problem"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="e.g. my screen flickers after the update"
            autoComplete="off"
          />
          <button type="submit" disabled={busy || draft.trim() === ""}>Send</button>
        </form>
      </main>

      <aside className="side">
        <PhoneSimulator screen={screen} />
      </aside>
    </div>
  );
}
