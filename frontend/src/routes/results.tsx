import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useScenario } from "@/state/scenario";
import {
  getRunArtifacts,
  getAlgorithmMetrics,
  getRunStatus,
  listRuns,
  plotUrl,
  fileUrl,
  type AlgorithmMetric,
  type ArtifactEntry,
  type RunArtifacts,
  type Run,
} from "@/lib/uav-api";
import { RUN_ID_PATTERN, type AllowedFileFilename, type AllowedPlotFilename } from "@/api/client";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
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
    title: "Terrain",
    items: [
      { file: "terrain.png", label: "terrain.png" },
      { file: "terrain_3d.png", label: "terrain_3d.png" },
    ],
  },
  {
    title: "Sensor Placement",
    items: [
      { file: "sensors.png", label: "sensors.png" },
      { file: "suitability.png", label: "suitability.png" },
      { file: "layers.png", label: "layers.png" },
    ],
  },
  {
    title: "Final cost",
    items: [
      { file: "final_cost_heatmap.png", label: "final_cost_heatmap.png" },
      { file: "final_cost_binary.png", label: "final_cost_binary.png" },
    ],
  },
  {
    title: "Pathfinders plots",
    items: [
      { file: "dijkstra_path.png", label: "dijkstra_path.png" },
      { file: "astar_path.png", label: "astar_path.png" },
      { file: "theta_star_path.png", label: "theta_star_path.png" },
      { file: "dstar_lite_path.png", label: "dstar_lite_path.png" },
      { file: "ant_colony_path.png", label: "ant_colony_path.png" },
      { file: "genetic_path.png", label: "genetic_path.png" },
      { file: "monte_carlo_rl_path.png", label: "monte_carlo_rl_path.png" },
      { file: "lazy_3d_route.png", label: "lazy_3d_route.png" },
      { file: "lazy_3d_route_over_terrain.png", label: "lazy_3d_route_over_terrain.png" },
      { file: "lazy_3d_altitude_profile.png", label: "lazy_3d_altitude_profile.png" },
      { file: "lazy_3d_cost_profile.png", label: "lazy_3d_cost_profile.png" },
      { file: "lazy_3d_stats_summary.png", label: "lazy_3d_stats_summary.png" },
    ],
  },
  {
    title: "Comparison",
    items: [{ file: "algorithm_comparison.png", label: "algorithm_comparison.png" }],
  },
];

function titleForArtifact(filename: string) {
  return filename.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ");
}

function groupArtifactsByType(artifacts: RunArtifacts | null) {
  if (!artifacts) return { plots: [], csv: [], outputs: [] as ArtifactEntry[] };
  return {
    plots: artifacts.plots ?? [],
    csv: artifacts.csv ?? [],
    outputs: artifacts.outputs ?? [],
  };
}

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

function fmtNum(v?: number, digits = 1) {
  if (typeof v !== "number" || Number.isNaN(v)) return "—";
  return v.toFixed(digits);
}

function StatusBadge({ status }: { status?: string }) {
  const s = (status ?? "").toLowerCase();
  const cls =
    s === "running"
      ? "badge badge-running"
      : s === "completed"
        ? "badge badge-completed"
        : s === "failed"
          ? "badge badge-failed"
          : "badge badge-queued";
  return <span className={cls}>{s || "unknown"}</span>;
}

function ResultsPage() {
  const { clientId } = useScenario();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const [runs, setRuns] = useState<Run[]>([]);
  const [current, setCurrent] = useState<Run | null>(null);
  const [metrics, setMetrics] = useState<AlgorithmMetric[] | null>(null);
  const [artifacts, setArtifacts] = useState<RunArtifacts | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [viewer, setViewer] = useState<{ url: string; label: string } | null>(null);
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
        setArtifacts(await getRunArtifacts(id));
      } else {
        setMetrics(null);
        setArtifacts(null);
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
            setArtifacts(await getRunArtifacts(selectedId));
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
  const artifactGroups = useMemo(() => groupArtifactsByType(artifacts), [artifacts]);
  const openViewer = useCallback((url: string, label: string) => {
    setViewer({ url, label });
  }, []);
  const closeViewer = useCallback(() => {
    setViewer(null);
  }, []);

  return (
    <div className="page page-results">
      <header className="app-header">
        <h1>Run Results</h1>
        <div className="subtitle">
          Inspect run status, algorithm metrics, plots, and downloadable run files.
        </div>
      </header>

      {err && <div className="alert alert-error">{err}</div>}

      <div className="layout">
        <div>
          <section className="panel">
            <div className="panel-header">Recent Runs</div>
            <div className="panel-body no-pad">
              {runs.length === 0 ? (
                <div style={{ padding: 14 }}>
                  <div className="empty-state">No runs for this client yet.</div>
                </div>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Run ID</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.slice(0, 30).map((r) => (
                      <tr key={r.runId} className={r.runId === selectedId ? "selected" : ""}>
                        <td className="mono">{r.runId.slice(0, 10)}â€¦</td>
                        <td>
                          <StatusBadge status={r.status} />
                        </td>
                        <td className="mono">{fmtTime(r.createdAt)}</td>
                        <td style={{ textAlign: "right" }}>
                          <button className="btn btn-sm" onClick={() => select(r.runId)}>
                            View
                          </button>
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
                <div className="empty-state">
                  Select a run from the list or launch a new one from Simulation.
                </div>
              ) : (
                <>
                  <dl className="summary-grid">
                    <dt>Run ID</dt>
                    <dd>{current.runId}</dd>
                    <dt>Status</dt>
                    <dd>
                      <StatusBadge status={current.status} />
                    </dd>
                    <dt>Created</dt>
                    <dd>{fmtTime(current.createdAt)}</dd>
                    <dt>Started</dt>
                    <dd>{fmtTime(current.startedAt)}</dd>
                    <dt>Finished</dt>
                    <dd>{fmtTime(current.finishedAt)}</dd>
                    <dt>Duration</dt>
                    <dd>{fmtDur(current.durationMs, current)}</dd>
                  </dl>
                  {current.status === "failed" && current.error && (
                    <div className="alert alert-error" style={{ marginTop: 12 }}>
                      {current.error}
                    </div>
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
                  <PlotGrid runId={current.runId} artifacts={artifactGroups.plots} onOpen={openViewer} />
                </div>
              </section>
              <section className="panel">
                <div className="panel-header">Downloads</div>
                <div className="panel-body no-pad">
                  <Downloads runId={current.runId} artifacts={artifactGroups} />
                </div>
              </section>
            </>
          )}
        </div>
      </div>

      <Dialog open={Boolean(viewer)} onOpenChange={(open) => !open && closeViewer()}>
        <DialogContent className="plot-viewer">
          {viewer && (
            <>
              <DialogTitle>{viewer.label}</DialogTitle>
              <DialogDescription>Click outside the image to close the preview.</DialogDescription>
              <div className="plot-viewer-frame">
                <img src={viewer.url} alt={viewer.label} />
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
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
        <pre
          style={{
            margin: 0,
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            whiteSpace: "pre-wrap",
          }}
        >
          {JSON.stringify(cfg, null, 2)}
        </pre>
      </div>
    </section>
  );
}

function AlgorithmMetrics({ metrics }: { metrics: AlgorithmMetric[] | null }) {
  const rows = metrics ?? [];
  if (rows.length === 0) {
    return (
      <div style={{ padding: 12, color: "var(--color-text-muted)" }}>
        Algorithm metrics are not available for this run yet.
      </div>
    );
  }
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Algorithm</th>
          <th>Status</th>
          <th className="num">Route Cost</th>
          <th className="num">Runtime (ms)</th>
          <th className="num">Search Visits</th>
          <th className="num">Route Nodes</th>
          <th className="num">Route Steps</th>
          <th className="num">Distance (km)</th>
          <th className="num">Efficiency</th>
          <th className="num">Avg Cell Cost</th>
          <th>Success</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((m) => (
          <tr key={m.algorithm}>
            <td>{m.algorithm}</td>
            <td>{m.status ?? "—"}</td>
            <td className="num">{fmtNum(m.totalCost, 6)}</td>
            <td className="num">{fmtNum(m.runtimeMs)}</td>
            <td className="num">{fmtNum(m.nodesVisited)}</td>
            <td className="num">{fmtNum(m.pathNodeCount)}</td>
            <td className="num">{fmtNum(m.pathStepCount)}</td>
            <td className="num">{fmtNum(m.totalDistanceKm)}</td>
            <td className="num">{fmtNum(m.pathEfficiency)}</td>
            <td className="num">{fmtNum(m.averageCellCost ?? m.averageCost, 6)}</td>
            <td>{m.success === undefined ? "—" : m.success ? "yes" : "no"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PlotImg({
  file,
  url,
  onOpen,
}: {
  file: AllowedPlotFilename;
  url: string;
  onOpen: (url: string, label: string) => void;
}) {
  const [ok, setOk] = useState<boolean | null>(null);
  return (
    <button
      type="button"
      className="plot-card plot-card-button"
      onClick={() => onOpen(url, file)}
    >
      <div className="plot-card-title">{file}</div>
      {ok === false ? (
        <div className="plot-placeholder">Not available</div>
      ) : (
        <img
          src={url}
          alt={file}
          loading="lazy"
          onLoad={() => setOk(true)}
          onError={() => setOk(false)}
        />
      )}
    </button>
  );
}

function PlotGrid({
  runId,
  artifacts,
  onOpen,
}: {
  runId: string;
  artifacts: ArtifactEntry[];
  onOpen: (url: string, label: string) => void;
}) {
  const discovered = new Map(artifacts.map((entry) => [entry.filename, entry]));
  const [openGroups, setOpenGroups] = useState<string[]>(PLOT_GROUPS.map((g) => g.title));

  return (
    <Accordion
      type="multiple"
      className="plot-accordion"
      value={openGroups}
      onValueChange={(value) => setOpenGroups(value)}
    >
      {PLOT_GROUPS.map((group) => {
        const groupArtifacts = group.items
          .map((item) => discovered.get(item.file) ?? null)
          .filter(Boolean) as ArtifactEntry[];
        const hasDiscovery = artifacts.length > 0;

        return (
          <AccordionItem key={group.title} value={group.title}>
            <AccordionTrigger>{group.title}</AccordionTrigger>
            <AccordionContent>
              <div className="plot-grid">
                {(hasDiscovery ? groupArtifacts : group.items.map((item) => ({ filename: item.file, label: item.label, url: plotUrl(runId, item.file) }))).map(
                  (plot) => (
                    <button
                      key={plot.filename}
                      type="button"
                      className="plot-card plot-card-button"
                      onClick={() => onOpen(plot.url, plot.label || titleForArtifact(plot.filename))}
                    >
                      <div className="plot-card-title">
                        {plot.label || titleForArtifact(plot.filename)}
                      </div>
                      <img src={plot.url} alt={plot.label || plot.filename} loading="lazy" />
                    </button>
                  ),
                )}
                {hasDiscovery && groupArtifacts.length === 0 && (
                  <div className="plot-placeholder">Plot unavailable</div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        );
      })}
    </Accordion>
  );
}

function Downloads({
  runId,
  artifacts,
}: {
  runId: string;
  artifacts: { csv: ArtifactEntry[]; outputs: ArtifactEntry[] };
}) {
  const groups: { title: string; files: AllowedFileFilename[] }[] = [
    {
      title: "Input CSVs",
      files: ["terrain_height.csv", "terrain_type.csv", "sensor.csv", "nfz.csv", "env.csv"],
    },
    { title: "Output CSVs", files: ["final_cost.csv"] },
  ];
  const discoveredCsv = artifacts.csv.length
    ? artifacts.csv
    : null;
  const discoveredOutputs = artifacts.outputs.length
    ? artifacts.outputs
    : null;
  return (
    <>
      {discoveredCsv || discoveredOutputs ? (
        <>
          {discoveredCsv?.length ? (
            <div>
              <div className="section-header">Discovered CSV / JSON</div>
              <ul style={{ margin: 0, padding: "10px 14px", listStyle: "none" }}>
                {discoveredCsv.map((entry) => (
                  <li key={entry.filename} style={{ padding: "3px 0" }}>
                    <a href={entry.url} target="_blank" rel="noreferrer" className="mono">
                      {entry.label || entry.filename}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {discoveredOutputs?.length ? (
            <div>
              <div className="section-header">Discovered Outputs</div>
              <ul style={{ margin: 0, padding: "10px 14px", listStyle: "none" }}>
                {discoveredOutputs.map((entry) => (
                  <li key={entry.filename} style={{ padding: "3px 0" }}>
                    <a href={entry.url} target="_blank" rel="noreferrer" className="mono">
                      {entry.label || entry.filename}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      ) : (
        groups.map((g) => (
        <div key={g.title}>
          <div className="section-header">{g.title}</div>
          <ul style={{ margin: 0, padding: "10px 14px", listStyle: "none" }}>
            {g.files.map((f) => (
              <li key={f} style={{ padding: "3px 0" }}>
                <a href={fileUrl(runId, f)} target="_blank" rel="noreferrer" className="mono">
                  {f}
                </a>
              </li>
            ))}
          </ul>
        </div>
        ))
      )}
      <div style={{ padding: 10, fontSize: 11, color: "var(--color-text-muted)" }}>
        Links open the backend file endpoint. Missing files return a backend 404.
      </div>
    </>
  );
}


