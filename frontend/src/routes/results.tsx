import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { useScenario } from "@/state/scenario";
import {
  getAlgorithmMetrics,
  getRunStatus,
  listRuns,
  plotUrl,
  fileUrl,
  type AlgorithmMetric,
  type Run,
} from "@/lib/uav-api";
import { RUN_ID_PATTERN, type AllowedFileFilename, type AllowedPlotFilename } from "@/api/client";
import { z } from "zod";

const searchSchema = z.object({
  runId: z.string().regex(RUN_ID_PATTERN, "Invalid run ID.").optional(),
});

export const Route = createFileRoute("/results")({
  validateSearch: (s) => searchSchema.parse(s),
  component: ResultsPage,
});

const PLOT_GROUPS: { title: string; items: { file: AllowedPlotFilename; label: string }[] }[] = [
  {
    title: "Environment Outputs",
    items: [
      { file: "terrain.png", label: "terrain.png" },
      { file: "terrain_3d.png", label: "terrain_3d.png" },
      { file: "sensors.png", label: "sensors.png" },
    ],
  },
  {
    title: "Threat Modeling Outputs",
    items: [
      { file: "suitability.png", label: "suitability.png" },
      { file: "layers.png", label: "layers.png" },
    ],
  },
  {
    title: "Final Computation Outputs",
    items: [
      { file: "final_cost_heatmap.png", label: "final_cost_heatmap.png" },
      { file: "final_cost_binary.png", label: "final_cost_binary.png" },
    ],
  },
];

function fmtTime(v?: string) {
  if (!v) return "—";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return v;
  return d.toISOString().replace("T", " ").slice(0, 19);
}

function fmtDur(ms?: number, run?: Run) {
  if (typeof ms === "number") return `${(ms / 1000).toFixed(1)} s`;
  if (run?.startedAt && run?.finishedAt) {
    const d = new Date(run.finishedAt).getTime() - new Date(run.startedAt).getTime();
    if (!Number.isNaN(d) && d >= 0) return `${(d / 1000).toFixed(1)} s`;
  }
  return "—";
}

function fmtNum(v?: number) {
  if (typeof v !== "number" || Number.isNaN(v)) return "—";
  return v.toFixed(1);
}

function StatusBadge({ status }: { status?: string }) {
  const s = (status ?? "").toLowerCase();
  const cls =
    s === "running" ? "badge badge-running" :
    s === "completed" ? "badge badge-completed" :
    s === "failed" ? "badge badge-failed" : "badge badge-queued";
  return <span className={cls}>{s || "unknown"}</span>;
}

function ResultsPage() {
  const { clientId } = useScenario();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const [runs, setRuns] = useState<Run[]>([]);
  const [current, setCurrent] = useState<Run | null>(null);
  const [metrics, setMetrics] = useState<AlgorithmMetric[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const refreshRuns = useCallback(async () => {
    if (!clientId) return;
    try {
      const rs = await listRuns(clientId);
      const sorted = [...rs].sort((a, b) => (b.createdAt ?? "").localeCompare(a.createdAt ?? ""));
      setRuns(sorted);
    } catch (e) {
      setErr((e as Error).message);
    }
  }, [clientId]);

  useEffect(() => {
    void refreshRuns();
  }, [refreshRuns]);

  const selectedId = search.runId;
  const loadRun = useCallback(async (id: string) => {
    setErr(null);
    try {
      const r = await getRunStatus(id);
      setCurrent(r);
      if (r.status === "completed") {
        const m = await getAlgorithmMetrics(id);
        setMetrics(m);
      } else {
        setMetrics(null);
      }
    } catch (e) {
      setErr((e as Error).message);
    }
  }, []);

  useEffect(() => {
    if (selectedId) void loadRun(selectedId);
    else setCurrent(null);
  }, [selectedId, loadRun]);

  useEffect(() => {
    if (pollRef.current) window.clearInterval(pollRef.current);
    if (!selectedId) return;
    const s = current?.status;
    if (s === "completed" || s === "failed") return;
    pollRef.current = window.setInterval(async () => {
      try {
        const r = await getRunStatus(selectedId);
        setCurrent((prev) => ({ ...(prev ?? {}), ...r }));
        if (r.status === "completed" || r.status === "failed") {
          if (pollRef.current) window.clearInterval(pollRef.current);
          void refreshRuns();
          if (r.status === "completed") {
            const m = await getAlgorithmMetrics(selectedId);
            setMetrics(m);
          }
        }
      } catch (e) {
        setErr((e as Error).message);
      }
    }, 2000);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [selectedId, current?.status, refreshRuns]);

  const select = (id: string) => navigate({ search: { runId: id } });

  return (
    <div className="page">
      <header className="app-header">
        <h1>Run Results</h1>
        <div className="subtitle">Inspect run status, algorithm metrics, plots, and downloadable run files.</div>
      </header>

      {err && <div className="alert alert-error">{err}</div>}

      <div className="layout">
        <div>
          <section className="panel">
            <div className="panel-header">Recent Runs</div>
            <div className="panel-body no-pad">
              {runs.length === 0 ? (
                <div style={{ padding: 14 }}><div className="empty-state">No runs for this client yet.</div></div>
              ) : (
                <table className="table">
                  <thead><tr><th>Run ID</th><th>Status</th><th>Created</th><th></th></tr></thead>
                  <tbody>
                    {runs.slice(0, 30).map((r) => (
                      <tr key={r.runId} className={r.runId === selectedId ? "selected" : ""}>
                        <td className="mono">{r.runId.slice(0, 10)}…</td>
                        <td><StatusBadge status={r.status} /></td>
                        <td className="mono">{fmtTime(r.createdAt)}</td>
                        <td style={{ textAlign: "right" }}>
                          <button className="btn btn-sm" onClick={() => select(r.runId)}>View</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        </div>

        <div>
          <section className="panel">
            <div className="panel-header">Current Run Summary</div>
            <div className="panel-body">
              {!current ? (
                <div className="empty-state">Select a run from the list or launch a new one from Simulation.</div>
              ) : (
                <>
                  <dl className="summary-grid">
                    <dt>Run ID</dt><dd>{current.runId}</dd>
                    <dt>Status</dt><dd><StatusBadge status={current.status} /></dd>
                    <dt>Created</dt><dd>{fmtTime(current.createdAt)}</dd>
                    <dt>Started</dt><dd>{fmtTime(current.startedAt)}</dd>
                    <dt>Finished</dt><dd>{fmtTime(current.finishedAt)}</dd>
                    <dt>Duration</dt><dd>{fmtDur(current.durationMs, current)}</dd>
                  </dl>
                  {current.status === "failed" && current.error && (
                    <div className="alert alert-error" style={{ marginTop: 12 }}>{current.error}</div>
                  )}
                </>
              )}
            </div>
          </section>

          {current && <ScenarioSummary run={current} />}

          {current?.status === "completed" && (
            <>
              <section className="panel">
                <div className="panel-header">Algorithm Metrics</div>
                <div className="panel-body no-pad">
                  <AlgorithmMetrics metrics={metrics} />
                </div>
              </section>
              <section className="panel">
                <div className="panel-header">Plots</div>
                <div className="panel-body no-pad">
                  <PlotGrid runId={current.runId} />
                </div>
              </section>
              <section className="panel">
                <div className="panel-header">Downloads</div>
                <div className="panel-body no-pad">
                  <Downloads runId={current.runId} />
                </div>
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function ScenarioSummary({ run }: { run: Run }) {
  const cfg = run.config as Record<string, unknown> | undefined;
  if (!cfg) return null;
  return (
    <section className="panel">
      <div className="panel-header">Scenario Summary</div>
      <div className="panel-body">
        <pre style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: 12, whiteSpace: "pre-wrap" }}>
          {JSON.stringify(cfg, null, 2)}
        </pre>
      </div>
    </section>
  );
}

function AlgorithmMetrics({ metrics }: { metrics: AlgorithmMetric[] | null }) {
  const rows = metrics ?? [];
  if (rows.length === 0) {
    return <div style={{ padding: 12, color: "var(--color-text-muted)" }}>Algorithm metrics are not available for this run yet.</div>;
  }
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Algorithm</th>
          <th>Status</th>
          <th className="num">Total Cost</th>
          <th className="num">Runtime (ms)</th>
          <th className="num">Nodes Visited</th>
          <th className="num">Path Nodes</th>
          <th className="num">Distance (km)</th>
          <th>Success</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((m) => (
          <tr key={m.algorithm}>
            <td>{m.algorithm}</td>
            <td>{m.status ?? "—"}</td>
            <td className="num">{fmtNum(m.totalCost)}</td>
            <td className="num">{fmtNum(m.runtimeMs)}</td>
            <td className="num">{fmtNum(m.nodesVisited)}</td>
            <td className="num">{fmtNum(m.pathNodeCount)}</td>
            <td className="num">{fmtNum(m.totalDistanceKm)}</td>
            <td>{m.success === undefined ? "—" : (m.success ? "yes" : "no")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PlotImg({ runId, file }: { runId: string; file: AllowedPlotFilename }) {
  const [ok, setOk] = useState<boolean | null>(null);
  return (
    <div className="plot-card">
      <div className="plot-card-title">{file}</div>
      {ok === false ? (
        <div className="plot-placeholder">Not available</div>
      ) : (
        <img
          src={plotUrl(runId, file)}
          alt={file}
          loading="lazy"
          onLoad={() => setOk(true)}
          onError={() => setOk(false)}
        />
      )}
    </div>
  );
}

function PlotGrid({ runId }: { runId: string }) {
  return (
    <>
      {PLOT_GROUPS.map((g) => (
        <div key={g.title}>
          <div className="plot-section-title">{g.title}</div>
          <div className="plot-grid">
            {g.items.map((it) => <PlotImg key={it.file} runId={runId} file={it.file} />)}
          </div>
        </div>
      ))}
    </>
  );
}

function Downloads({ runId }: { runId: string }) {
  const groups: { title: string; files: AllowedFileFilename[] }[] = [
    { title: "Input CSVs", files: ["terrain_height.csv", "terrain_type.csv", "sensor.csv", "nfz.csv", "env.csv"] },
    { title: "Output CSVs", files: ["final_cost.csv"] },
  ];
  return (
    <>
      {groups.map((g) => (
        <div key={g.title}>
          <div className="section-header">{g.title}</div>
          <ul style={{ margin: 0, padding: "10px 14px", listStyle: "none" }}>
            {g.files.map((f) => (
              <li key={f} style={{ padding: "3px 0" }}>
                <a href={fileUrl(runId, f)} target="_blank" rel="noreferrer" className="mono">{f}</a>
              </li>
            ))}
          </ul>
        </div>
      ))}
      <div style={{ padding: 10, fontSize: 11, color: "var(--color-text-muted)" }}>
        Links open the backend file endpoint. Missing files return a backend 404.
      </div>
    </>
  );
}