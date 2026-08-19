import { useState } from "react";

const BASE = import.meta.env.VITE_PLATFORM_BASE || "http://localhost:8000";
const KEY = import.meta.env.VITE_PLATFORM_KEY || "dev-key";

async function api(path, body) {
  const res = await fetch(BASE + path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json", "X-API-Key": KEY },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

export default function ControlPanel() {
  const [goal, setGoal] = useState("");
  const [run, setRun] = useState(null);
  const [trace, setTrace] = useState(null);

  async function onRun(e) {
    e.preventDefault();
    // Assumes a "research" agent was registered once at setup.
    const r = await api("/runs", { agent_id: "research", goal });
    setRun(r);
    if (r.trace_id) setTrace(await api(`/runs/${r.trace_id}`));
  }

  return (
    <div className="panel">
      <h2>Run an agent</h2>
      <form onSubmit={onRun}>
        <input value={goal} onChange={(e) => setGoal(e.target.value)}
               placeholder="Give the agent a goal…" />
        <button>Run</button>
      </form>

      {run && (
        <div className="result">
          <p><strong>Answer:</strong> {run.answer}</p>
          <p className="meta">
            {run.steps} steps · {run.terminated}
          </p>
        </div>
      )}

      {trace && (
        <div className="trace">
          <h3>Run trace</h3>
          <p>
            {trace.skill_calls} skill calls · {trace.failed_calls} failed ·{" "}
            {trace.total_latency_ms} ms · {trace.grounded ? "grounded ✓" : "ungrounded"}
          </p>
        </div>
      )}
    </div>
  );
}
