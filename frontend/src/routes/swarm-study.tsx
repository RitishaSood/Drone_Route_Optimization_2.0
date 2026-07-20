import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { useScenario } from "@/state/scenario";
import {
  getRunArtifacts,
  getSwarmSummary,
  listRuns,
  runSwarmSimulation,
  type Run,
  type RunArtifacts,
  type SwarmConfig,
  type SwarmSummaryRow,
} from "@/lib/uav-api";

export const Route = createFileRoute("/swarm-study")({
  component: SwarmStudyPage,
});

const DEFAULT_SWARM_CONFIG: SwarmConfig = {
  swarmEnabled: true,
  swarmSizes: [1, 2, 4, 8, 16],
  numMonteCarloTrials: 1000,
  strategies: ["single_route", "split_routes", "decoy_lead", "distributed_routing"],
  requiredSurvivors: 1,
  targetCoverageThreshold: 0.7,
  decoyFraction: 0.25,
  radarDetectionScaleMin: 0.8,
  radarDetectionScaleMax: 1.2,
  samKillProbabilityMin: 0.3,
  samKillProbabilityMax: 0.8,
  ewEffectivenessMin: 0.2,
  ewEffectivenessMax: 0.9,
  communicationLossMin: 0.05,
  communicationLossMax: 0.4,
  weatherSeverityMin: 0.0,
  weatherSeverityMax: 1.0,
};

function parseCsvList(value: string) {
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function SwarmStudyPage() {
  const { clientId } = useScenario();
  const [runs, setRuns] = useState<Run[]>([]);
  const [runId, setRunId] = useState("");
  const [config, setConfig] = useState<SwarmConfig>(DEFAULT_SWARM_CONFIG);
  const [summary, setSummary] = useState<SwarmSummaryRow[]>([]);
  const [artifacts, setArtifacts] = useState<RunArtifacts | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      if (!clientId) return;
      try {
        const rs = await listRuns(clientId);
        setRuns(rs);
        if (!runId && rs[0]?.runId) setRunId(rs[0].runId);
      } catch (e) {
        setError((e as Error).message);
      }
    })();
  }, [clientId, runId]);

  const selectedRun = useMemo(() => runs.find((run) => run.runId === runId) ?? null, [runs, runId]);

  const runStudy = async () => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    try {
      await runSwarmSimulation(runId, config);
      const result = await getSwarmSummary(runId);
      setSummary(result?.summary ?? []);
      setArtifacts(await getRunArtifacts(runId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="app-header">
        <h1>Swarm Study</h1>
        <div className="subtitle">
          Compare how swarm size and route strategy affect mission success under threat uncertainty.
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="layout">
        <section className="panel">
          <div className="panel-header">Study Inputs</div>
          <div className="panel-body">
            <div className="form-grid">
              <div>
                <label htmlFor="runId">Run</label>
                <select id="runId" value={runId} onChange={(e) => setRunId(e.target.value)}>
                  <option value="">Select a run</option>
                  {runs.map((run) => (
                    <option key={run.runId} value={run.runId}>
                      {run.runId}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="swarmSizes">Swarm Sizes</label>
                <input
                  id="swarmSizes"
                  value={(config.swarmSizes ?? []).join(", ")}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      swarmSizes: parseCsvList(e.target.value)
                        .map((v) => Number(v))
                        .filter((v) => Number.isFinite(v) && v > 0),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="numMonteCarloTrials">Monte Carlo Trials</label>
                <input
                  id="numMonteCarloTrials"
                  type="number"
                  min={1}
                  step={1}
                  value={config.numMonteCarloTrials ?? 1000}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      numMonteCarloTrials: parseInt(e.target.value || "1000", 10),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="strategies">Strategies to Compare</label>
                <input
                  id="strategies"
                  value={(config.strategies ?? []).join(", ")}
                  onChange={(e) =>
                    setConfig({ ...config, strategies: parseCsvList(e.target.value) })
                  }
                />
              </div>
              <div>
                <label htmlFor="requiredSurvivors">Required Survivors</label>
                <input
                  id="requiredSurvivors"
                  type="number"
                  min={1}
                  step={1}
                  value={config.requiredSurvivors ?? 1}
                  onChange={(e) =>
                    setConfig({ ...config, requiredSurvivors: parseInt(e.target.value || "1", 10) })
                  }
                />
              </div>
              <div>
                <label htmlFor="targetCoverageThreshold">Target Coverage Threshold</label>
                <input
                  id="targetCoverageThreshold"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.targetCoverageThreshold ?? 0.7}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      targetCoverageThreshold: parseFloat(e.target.value || "0.7"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="decoyFraction">Decoy Fraction</label>
                <input
                  id="decoyFraction"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.decoyFraction ?? 0.25}
                  onChange={(e) =>
                    setConfig({ ...config, decoyFraction: parseFloat(e.target.value || "0.25") })
                  }
                />
              </div>
              <div>
                <label htmlFor="radarDetectionScaleMin">Radar Detection Scale Min</label>
                <input
                  id="radarDetectionScaleMin"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.radarDetectionScaleMin ?? 0.8}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      radarDetectionScaleMin: parseFloat(e.target.value || "0.8"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="radarDetectionScaleMax">Radar Detection Scale Max</label>
                <input
                  id="radarDetectionScaleMax"
                  type="number"
                  min={0}
                  max={2}
                  step={0.01}
                  value={config.radarDetectionScaleMax ?? 1.2}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      radarDetectionScaleMax: parseFloat(e.target.value || "1.2"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="samKillProbabilityMin">SAM Kill Probability Min</label>
                <input
                  id="samKillProbabilityMin"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.samKillProbabilityMin ?? 0.3}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      samKillProbabilityMin: parseFloat(e.target.value || "0.3"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="samKillProbabilityMax">SAM Kill Probability Max</label>
                <input
                  id="samKillProbabilityMax"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.samKillProbabilityMax ?? 0.8}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      samKillProbabilityMax: parseFloat(e.target.value || "0.8"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="ewEffectivenessMin">EW Effectiveness Min</label>
                <input
                  id="ewEffectivenessMin"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.ewEffectivenessMin ?? 0.2}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      ewEffectivenessMin: parseFloat(e.target.value || "0.2"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="ewEffectivenessMax">EW Effectiveness Max</label>
                <input
                  id="ewEffectivenessMax"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.ewEffectivenessMax ?? 0.9}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      ewEffectivenessMax: parseFloat(e.target.value || "0.9"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="communicationLossMin">Communication Loss Min</label>
                <input
                  id="communicationLossMin"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.communicationLossMin ?? 0.05}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      communicationLossMin: parseFloat(e.target.value || "0.05"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="communicationLossMax">Communication Loss Max</label>
                <input
                  id="communicationLossMax"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.communicationLossMax ?? 0.4}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      communicationLossMax: parseFloat(e.target.value || "0.4"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="weatherSeverityMin">Weather Severity Min</label>
                <input
                  id="weatherSeverityMin"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.weatherSeverityMin ?? 0.0}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      weatherSeverityMin: parseFloat(e.target.value || "0.0"),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="weatherSeverityMax">Weather Severity Max</label>
                <input
                  id="weatherSeverityMax"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={config.weatherSeverityMax ?? 1.0}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      weatherSeverityMax: parseFloat(e.target.value || "1.0"),
                    })
                  }
                />
              </div>
            </div>
            <div className="row" style={{ marginTop: 12 }}>
              <button className="btn btn-primary" disabled={!runId || loading} onClick={runStudy}>
                {loading ? "Running..." : "Run Swarm Study"}
              </button>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">Results</div>
          <div className="panel-body">
            {!summary.length ? (
              <div className="empty-state">Run a study to see strategy comparisons.</div>
            ) : (
              <>
                <dl className="summary-grid">
                  <dt>Selected Run</dt>
                  <dd>{selectedRun?.runId ?? runId}</dd>
                  <dt>Best Strategy</dt>
                  <dd>
                    {summary.sort(
                      (a, b) => b.missionSuccessProbability - a.missionSuccessProbability,
                    )[0]?.strategy ?? "-"}
                  </dd>
                  <dt>Best Swarm Size</dt>
                  <dd>
                    {summary.sort(
                      (a, b) => b.missionSuccessProbability - a.missionSuccessProbability,
                    )[0]?.swarmSize ?? "-"}
                  </dd>
                </dl>
                <table className="table" style={{ marginTop: 12 }}>
                  <thead>
                    <tr>
                      <th>Strategy</th>
                      <th>Swarm</th>
                      <th>Success</th>
                      <th>Survivors</th>
                      <th>Coverage</th>
                      <th>Cost</th>
                      <th>Cost / Success</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.map((row) => (
                      <tr key={`${row.strategy}-${row.swarmSize}`}>
                        <td>{row.strategy}</td>
                        <td>{row.swarmSize}</td>
                        <td>{(row.missionSuccessProbability * 100).toFixed(1)}%</td>
                        <td>{row.averageSurvivingDrones.toFixed(2)}</td>
                        <td>{(row.averageTargetCoverage * 100).toFixed(1)}%</td>
                        <td>{row.averageMissionCost.toFixed(2)}</td>
                        <td>
                          {row.costPerSuccessfulMission == null
                            ? "—"
                            : row.costPerSuccessfulMission.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {artifacts?.plots?.length ? (
                  <div className="artifact-grid" style={{ marginTop: 16 }}>
                    {artifacts.plots.map((plot) => (
                      <a key={plot.filename} href={plot.url} target="_blank" rel="noreferrer">
                        <img
                          src={plot.url}
                          alt={plot.label}
                          style={{ width: "100%", display: "block" }}
                        />
                        <div style={{ padding: 8 }}>{plot.label}</div>
                      </a>
                    ))}
                  </div>
                ) : null}
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
