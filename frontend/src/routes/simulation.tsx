import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { DEFAULT_CONFIG, useScenario, type ValidationIssue } from "@/state/scenario";
import { DRONE_NAMES, DRONE_BY_NAME } from "@/data/drones";
import { csvToObjects, objectsToCsv } from "@/lib/csv";
import { createRun, type ScenarioConfig, type SensorRow } from "@/lib/uav-api";

export const Route = createFileRoute("/simulation")({
  component: SimulationPage,
});

const MAX_CSV_FILE_SIZE_BYTES = 5 * 1024 * 1024;
const CSV_WARNING_TEXT =
  "CSV content is treated as plain text. Spreadsheet formula-like cells are escaped during export.";

const TABS = [
  "Mission",
  "Route",
  "Terrain",
  "Threats",
  "Environment",
  "EW",
  "Sensors",
  "Algorithms",
  "UAV",
  "Input Mode",
  "Review",
] as const;
type TabName = (typeof TABS)[number];

const THREAT_OPTIONS = [
  { value: "radar", label: "Radar" },
  { value: "ir", label: "Infrared" },
  { value: "acoustic", label: "Acoustic" },
  { value: "visual", label: "Visual" },
];

const PLACEMENT_MODES = ["greedy", "random", "strategic"] as const;

function errorFor(issues: ValidationIssue[], field: string) {
  return issues.find((i) => i.field === field)?.message;
}

function SimulationPage() {
  const {
    clientId,
    config,
    patch,
    reset,
    issues,
    reviewVisited,
    markReviewVisited,
    confirmed,
    setConfirmed,
  } = useScenario();
  const [tab, setTab] = useState<TabName>("Mission");
  const [planningModeConfirmed, setPlanningModeConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const navigate = useNavigate();

  const blocking = issues.filter((i) => i.blocking);
  const canRun = blocking.length === 0 && reviewVisited && confirmed && !submitting;

  const currentStep = !reviewVisited ? 1 : blocking.length > 0 ? 2 : !confirmed ? 3 : 4;
  const modeLocked = planningModeConfirmed;

  const handleTab = (t: TabName) => {
    setTab(t);
    if (t === "Review") markReviewVisited();
  };

  const handleSubmit = async () => {
    if (!canRun) return;
    setSubmitting(true);
    setApiError(null);
    try {
      const run = await createRun(clientId, config);
      navigate({ to: "/results", search: { runId: run.runId } });
    } catch (e) {
      setApiError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    reset();
    setTab("Mission");
    setPlanningModeConfirmed(false);
  };

  const uploadModes = config.inputMode !== "generated" || config.sensorMode === "uploaded";
  const uploadUnavailable = uploadModes; // frontend cannot yet upload; backend support required

  return (
    <div className="page">
      <header className="app-header">
        <h1>Simulation Setup</h1>
        <div className="subtitle">
          Configure scenario, validate inputs, review, and run all supported route-planning
          algorithms.
        </div>
      </header>

      <div className="step-strip" role="list">
        {["Configure", "Validate", "Preview", "Confirm & Run"].map((label, i) => (
          <div
            key={label}
            role="listitem"
            className={`step ${currentStep === i + 1 ? "active" : ""}`}
          >
            <span className="num">{i + 1}</span>
            <span>{label}</span>
          </div>
        ))}
      </div>

      {apiError && (
        <div className="alert alert-error" role="alert">
          {apiError}
        </div>
      )}

      <section className="panel">
        <div className="panel-header">Planning Mode</div>
        <div className="panel-body stack">
          <div className="field-hint">
            Select the mission planning mode first. After you confirm it, the scenario tabs below
            become available and the mode stays fixed until reset.
          </div>
          <div className="mode-select">
            {(
              [
                [
                  "2.5D",
                  "2.5D",
                  "Fixed-altitude route planning with derived start and end Z values.",
                ],
                ["3D", "3D", "Lazy 3D A* with editable endpoint Z values."],
              ] as const
            ).map(([value, label, desc]) => (
              <label key={value} className={config.planningMode === value ? "selected" : ""}>
                <input
                  type="radio"
                  name="planningMode"
                  checked={config.planningMode === value}
                  disabled={modeLocked}
                  onChange={() => patch({ planningMode: value })}
                />
                <span>
                  <strong>{label}</strong>
                  <span className="mode-desc">{desc}</span>
                </span>
              </label>
            ))}
          </div>
          <div className="row">
            <button
              className="btn btn-primary"
              onClick={() => setPlanningModeConfirmed(true)}
              disabled={modeLocked}
            >
              {modeLocked ? "Mode confirmed" : "Confirm mode"}
            </button>
            <div className="field-hint" style={{ margin: 0, alignSelf: "center" }}>
              {modeLocked ? "Mode is locked until reset." : "Confirm the mode to continue."}
            </div>
            <button
              className="btn"
              onClick={() => {
                reset();
                setTab("Mission");
                setPlanningModeConfirmed(false);
              }}
              disabled={!modeLocked && config.planningMode === DEFAULT_CONFIG.planningMode}
            >
              Reset mode
            </button>
          </div>
        </div>
      </section>

      {modeLocked && (
        <section className="panel">
          <div className="panel-header">Scenario Configuration</div>
          <div className="tabs" role="tablist">
            {TABS.map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                className={`tab ${tab === t ? "active" : ""}`}
                onClick={() => handleTab(t)}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="panel-body">
            {tab === "Mission" && <MissionTab />}
            {tab === "Route" && <RouteTab />}
            {tab === "Terrain" && <TerrainTab />}
            {tab === "Threats" && <ThreatsTab />}
            {tab === "Environment" && <EnvironmentTab />}
            {tab === "EW" && <EwTab />}
            {tab === "Sensors" && <SensorsTab />}
            {tab === "Algorithms" && <AlgorithmsTab />}
            {tab === "UAV" && <UavTab />}
            {tab === "Input Mode" && <InputModeTab />}
            {tab === "Review" && (
              <ReviewTab
                issues={issues}
                reviewVisited={reviewVisited}
                confirmed={confirmed}
                onConfirm={setConfirmed}
                canRun={canRun}
                onRun={handleSubmit}
                onReset={handleReset}
                submitting={submitting}
                uploadUnavailable={uploadUnavailable}
              />
            )}
          </div>
        </section>
      )}
    </div>
  );
}

/* ---------- Tabs ---------- */

function MissionTab() {
  const { config, patch, issues } = useScenario();
  const is3d = config.planningMode === "3D";
  return (
    <div>
      <dl className="readonly-list" style={{ marginBottom: 16 }}>
        <dt>Grid size</dt>
        <dd>100 × 100</dd>
        <dt>Cell scale</dt>
        <dd>1 km per x/y cell</dd>
        <dt>Z scale</dt>
        <dd>100 m per z unit</dd>
        <dt>Current mode</dt>
        <dd>{is3d ? "3D route planning" : "2.5D route planning"}</dd>
      </dl>
      <div className="form-grid">
        <div>
          {is3d ? (
            <div className="stack">
              <NumField
                label="Start Z"
                id="startZ"
                v={config.route.start.z}
                min={0}
                max={100}
                onChange={(v) =>
                  patch({ route: { ...config.route, start: { ...config.route.start, z: v } } })
                }
              />
              <NumField
                label="End Z"
                id="endZ"
                v={config.route.end.z}
                min={0}
                max={100}
                onChange={(v) =>
                  patch({ route: { ...config.route, end: { ...config.route.end, z: v } } })
                }
              />
              <NumField
                label="Preferred Z"
                id="preferredZ"
                v={config.preferredZ ?? config.flightZ}
                min={0}
                max={100}
                onChange={(v) => patch({ preferredZ: v })}
              />
            </div>
          ) : (
            <>
              <label htmlFor="flightZ">Mission Z</label>
              <input
                id="flightZ"
                type="number"
                min={0}
                max={100}
                step={1}
                value={config.flightZ}
                onChange={(e) => patch({ flightZ: parseInt(e.target.value || "0", 10) })}
              />
              {errorFor(issues, "flightZ") ? (
                <div className="field-error">{errorFor(issues, "flightZ")}</div>
              ) : (
                <div className="field-hint">
                  This sets the derived route altitude for 2.5D planning.
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function RouteTab() {
  const { config, patch, issues } = useScenario();
  const { start, end } = config.route;
  const is3d = config.planningMode === "3D";
  const setStart = (p: Partial<typeof start>) =>
    patch({
      route: { ...config.route, start: { ...start, ...p, z: is3d ? start.z : config.flightZ } },
    });
  const setEnd = (p: Partial<typeof end>) =>
    patch({
      route: { ...config.route, end: { ...end, ...p, z: is3d ? end.z : config.flightZ } },
    });

  const dxKm = Math.abs(end.x - start.x);
  const dyKm = Math.abs(end.y - start.y);
  const distCells = Math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2);

  return (
    <div className="stack">
      <div className="field-hint">
        {is3d
          ? "Lazy 3D A* mode exposes editable start and end altitude fields."
          : "The current route model uses a fixed flight altitude. Start and end z values are inherited from the mission altitude."}
      </div>
      <div className="form-grid">
        <div>
          <div className="section-header" style={{ margin: "0 0 8px", padding: "6px 10px" }}>
            Start Point
          </div>
          <NumField
            label="Start X"
            id="startX"
            v={start.x}
            min={0}
            max={99}
            onChange={(v) => setStart({ x: v })}
            err={errorFor(issues, "route.start.x")}
          />
          <NumField
            label="Start Y"
            id="startY"
            v={start.y}
            min={0}
            max={99}
            onChange={(v) => setStart({ y: v })}
            err={errorFor(issues, "route.start.y")}
          />
          {is3d ? (
            <div className="stack">
              <NumField
                label="Start Z"
                id="routeStartZ"
                v={start.z}
                min={0}
                max={100}
                onChange={(v) => setStart({ z: v })}
              />
              {errorFor(issues, "route.start.z") && (
                <div className="field-error">{errorFor(issues, "route.start.z")}</div>
              )}
            </div>
          ) : (
            <div style={{ marginTop: 6 }}>
              <label>Start Z (derived)</label>
              <input readOnly value={start.z} />
            </div>
          )}
        </div>
        <div>
          <div className="section-header" style={{ margin: "0 0 8px", padding: "6px 10px" }}>
            End Point
          </div>
          <NumField
            label="End X"
            id="endX"
            v={end.x}
            min={0}
            max={99}
            onChange={(v) => setEnd({ x: v })}
            err={errorFor(issues, "route.end.x")}
          />
          <NumField
            label="End Y"
            id="endY"
            v={end.y}
            min={0}
            max={99}
            onChange={(v) => setEnd({ y: v })}
            err={errorFor(issues, "route.end.y")}
          />
          {is3d ? (
            <div className="stack">
              <NumField
                label="End Z"
                id="routeEndZ"
                v={end.z}
                min={0}
                max={100}
                onChange={(v) => setEnd({ z: v })}
              />
              {errorFor(issues, "route.end.z") && (
                <div className="field-error">{errorFor(issues, "route.end.z")}</div>
              )}
            </div>
          ) : (
            <div style={{ marginTop: 6 }}>
              <label>End Z (derived)</label>
              <input readOnly value={end.z} />
            </div>
          )}
        </div>
      </div>
      {errorFor(issues, "route") && <div className="field-error">{errorFor(issues, "route")}</div>}
      <dl className="readonly-list">
        <dt>Straight-line distance</dt>
        <dd>
          {distCells.toFixed(2)} cells ≈ {distCells.toFixed(2)} km
        </dd>
        <dt>Δx, Δy</dt>
        <dd>
          {dxKm} km, {dyKm} km
        </dd>
      </dl>
      {is3d && (
        <div className="form-grid" style={{ marginTop: 12 }}>
          <NumField
            label="Z Min"
            id="zMin"
            v={config.zMin ?? 0}
            min={0}
            max={100}
            onChange={(v) => patch({ zMin: v })}
          />
          <NumField
            label="Z Max"
            id="zMax"
            v={config.zMax ?? 100}
            min={0}
            max={100}
            onChange={(v) => patch({ zMax: v })}
          />
          <NumField
            label="Preferred Z"
            id="preferredZRoute"
            v={config.preferredZ ?? config.flightZ}
            min={0}
            max={100}
            onChange={(v) => patch({ preferredZ: v })}
          />
        </div>
      )}
    </div>
  );
}

function NumField({
  label,
  id,
  v,
  min,
  max,
  onChange,
  err,
}: {
  label: string;
  id: string;
  v: number;
  min: number;
  max: number;
  onChange: (v: number) => void;
  err?: string;
}) {
  return (
    <div style={{ marginTop: 6 }}>
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type="number"
        min={min}
        max={max}
        step={1}
        value={v}
        onChange={(e) => onChange(parseInt(e.target.value || "0", 10))}
      />
      {err ? (
        <div className="field-error">{err}</div>
      ) : (
        <div className="field-hint">
          Integer {min}–{max}.
        </div>
      )}
    </div>
  );
}

function TerrainTab() {
  const { config, patch, issues } = useScenario();
  return (
    <div className="stack">
      <div className="form-grid">
        <div>
          <label htmlFor="terrainSeed">Terrain seed</label>
          <input
            id="terrainSeed"
            type="number"
            min={0}
            max={2147483647}
            step={1}
            value={config.terrainSeed}
            onChange={(e) => patch({ terrainSeed: parseInt(e.target.value || "0", 10) })}
          />
          {errorFor(issues, "terrainSeed") ? (
            <div className="field-error">{errorFor(issues, "terrainSeed")}</div>
          ) : (
            <div className="field-hint">Deterministic seed for procedural terrain generation.</div>
          )}
        </div>
      </div>
      <div>
        <label>Terrain classes (read-only)</label>
        <div className="checkbox-group">
          {["water", "mountain", "forest", "plain", "hill", "valley"].map((c) => (
            <span key={c} className="chip">
              {c}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function ThreatsTab() {
  const { config, patch, issues } = useScenario();
  const toggle = (v: string) => {
    const has = config.threatTypes.includes(v);
    patch({
      threatTypes: has ? config.threatTypes.filter((t) => t !== v) : [...config.threatTypes, v],
    });
  };
  return (
    <div className="form-grid">
      <div className="full">
        <label>Threat types</label>
        <div className="checkbox-group">
          {THREAT_OPTIONS.map((o) => (
            <label key={o.value}>
              <input
                type="checkbox"
                checked={config.threatTypes.includes(o.value)}
                onChange={() => toggle(o.value)}
              />
              {o.label}
            </label>
          ))}
        </div>
        {errorFor(issues, "threatTypes") && (
          <div className="field-error">{errorFor(issues, "threatTypes")}</div>
        )}
      </div>
      <div>
        <label htmlFor="nfzCount">NFZ count</label>
        <input
          id="nfzCount"
          type="number"
          min={0}
          max={100}
          step={1}
          value={config.nfzCount}
          onChange={(e) => patch({ nfzCount: parseInt(e.target.value || "0", 10) })}
        />
        {errorFor(issues, "nfzCount") ? (
          <div className="field-error">{errorFor(issues, "nfzCount")}</div>
        ) : (
          <div className="field-hint">Integer 0–100.</div>
        )}
      </div>
    </div>
  );
}

function EnvironmentTab() {
  const { config, patch } = useScenario();
  const baseEnv = { ...(DEFAULT_CONFIG.environment ?? {}), ...(config.environment ?? {}) };
  const setEnv = (next: Partial<typeof baseEnv>) => patch({ environment: { ...baseEnv, ...next } });
  return (
    <div className="stack">
      <label>
        <input
          type="checkbox"
          checked={Boolean(config.environmentEnabled)}
          onChange={(e) => patch({ environmentEnabled: e.target.checked })}
        />
        Enable environmental effects
      </label>
      <div className="form-grid">
        <div className="stack">
          <label>
            <input
              type="checkbox"
              checked={Boolean(baseEnv.windEnabled)}
              onChange={(e) => setEnv({ windEnabled: e.target.checked })}
            />
            Wind
          </label>
          {baseEnv.windEnabled && (
            <div className="form-grid">
              <NumField
                label="Wind speed (m/s)"
                id="windSpeed"
                v={baseEnv.windSpeed}
                min={0}
                max={100}
                onChange={(v) => setEnv({ windSpeed: v })}
              />
              <NumField
                label="Wind direction"
                id="windDirection"
                v={baseEnv.windDirection}
                min={0}
                max={359}
                onChange={(v) => setEnv({ windDirection: v })}
              />
              <NumField
                label="Gust speed"
                id="gustSpeed"
                v={baseEnv.gustSpeed}
                min={0}
                max={100}
                onChange={(v) => setEnv({ gustSpeed: v })}
              />
            </div>
          )}
        </div>
        <div className="stack">
          <label>
            <input
              type="checkbox"
              checked={Boolean(baseEnv.rainEnabled)}
              onChange={(e) => setEnv({ rainEnabled: e.target.checked })}
            />
            Rain
          </label>
          {baseEnv.rainEnabled && (
            <DecimalField
              label="Rain intensity"
              id="rainIntensity"
              v={baseEnv.rainIntensity}
              min={0}
              max={1}
              step={0.1}
              onChange={(v) => setEnv({ rainIntensity: v })}
            />
          )}
        </div>
        <div className="stack">
          <label>
            <input
              type="checkbox"
              checked={Boolean(baseEnv.fogEnabled)}
              onChange={(e) => setEnv({ fogEnabled: e.target.checked })}
            />
            Fog
          </label>
          {baseEnv.fogEnabled && (
            <DecimalField
              label="Fog intensity"
              id="fogIntensity"
              v={baseEnv.fogIntensity}
              min={0}
              max={1}
              step={0.1}
              onChange={(v) => setEnv({ fogIntensity: v })}
            />
          )}
        </div>
        <div className="stack">
          <label>
            <input
              type="checkbox"
              checked={Boolean(baseEnv.temperatureEnabled)}
              onChange={(e) => setEnv({ temperatureEnabled: e.target.checked })}
            />
            Temperature
          </label>
          {baseEnv.temperatureEnabled && (
            <DecimalField
              label="Temperature C"
              id="temperatureC"
              v={baseEnv.temperatureC}
              min={-50}
              max={60}
              step={0.1}
              onChange={(v) => setEnv({ temperatureC: v })}
            />
          )}
        </div>
        <div className="stack">
          <label>
            <input
              type="checkbox"
              checked={Boolean(baseEnv.turbulenceEnabled)}
              onChange={(e) => setEnv({ turbulenceEnabled: e.target.checked })}
            />
            Turbulence
          </label>
          {baseEnv.turbulenceEnabled && (
            <DecimalField
              label="Turbulence intensity"
              id="turbulenceIntensity"
              v={baseEnv.turbulenceIntensity}
              min={0}
              max={1}
              step={0.1}
              onChange={(v) => setEnv({ turbulenceIntensity: v })}
            />
          )}
        </div>
      </div>
      <label>
        <input
          type="checkbox"
          checked={Boolean(baseEnv.thunderstormEnabled)}
          onChange={(e) => setEnv({ thunderstormEnabled: e.target.checked })}
        />
        Thunderstorm
      </label>
      <div className="field-hint">
        Environmental settings are passed through with the run config.
      </div>
    </div>
  );
}

function DecimalField({
  label,
  id,
  v,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  id: string;
  v: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <div style={{ marginTop: 6 }}>
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type="number"
        min={min}
        max={max}
        step={step}
        value={v}
        onChange={(e) => onChange(parseFloat(e.target.value || "0"))}
      />
      <div className="field-hint">
        Value {min} to {max}.
      </div>
    </div>
  );
}

function EwTab() {
  const { config, patch } = useScenario();
  return (
    <div className="stack">
      <label>
        <input
          type="checkbox"
          checked={Boolean(config.ewJammingEnabled)}
          onChange={(e) => patch({ ewJammingEnabled: e.target.checked })}
        />
        Enable EW jamming
      </label>
      <label>
        <input
          type="checkbox"
          checked={Boolean(config.advancedThreatFalloffEnabled)}
          onChange={(e) => patch({ advancedThreatFalloffEnabled: e.target.checked })}
        />
        Advanced threat falloff
      </label>
      <div className="form-grid">
        <NumField
          label="Radar R0"
          id="radarR0"
          v={config.falloffConfig?.radar?.R0 ?? 35}
          min={0}
          max={200}
          onChange={(v) =>
            patch({
              falloffConfig: {
                ...config.falloffConfig,
                radar: { ...(config.falloffConfig?.radar ?? {}), R0: v },
              },
            })
          }
        />
        <NumField
          label="Radar max range"
          id="radarMaxRange"
          v={config.falloffConfig?.radar?.maxRange ?? 60}
          min={0}
          max={200}
          onChange={(v) =>
            patch({
              falloffConfig: {
                ...config.falloffConfig,
                radar: { ...(config.falloffConfig?.radar ?? {}), maxRange: v },
              },
            })
          }
        />
        <NumField
          label="Radar floor probability"
          id="radarFloorProbability"
          v={Math.round((config.falloffConfig?.radar?.floorProbability ?? 0.02) * 1000)}
          min={0}
          max={1000}
          onChange={(v) =>
            patch({
              falloffConfig: {
                ...config.falloffConfig,
                radar: {
                  ...(config.falloffConfig?.radar ?? {}),
                  floorProbability: v / 1000,
                },
              },
            })
          }
        />
        <NumField
          label="EW weight"
          id="ewWeight"
          v={Math.round((config.falloffConfig?.ewJamming?.weight ?? 1) * 100)}
          min={0}
          max={500}
          onChange={(v) =>
            patch({
              falloffConfig: {
                ...config.falloffConfig,
                ewJamming: {
                  ...(config.falloffConfig?.ewJamming ?? {}),
                  weight: v / 100,
                },
              },
            })
          }
        />
      </div>
    </div>
  );
}

function AlgorithmsTab() {
  const { config, patch } = useScenario();
  const is3d = config.planningMode === "3D";
  const options = ["dijkstra", "astar", "ant-colony", "theta-star", "dstar-lite"] as const;
  useEffect(() => {
    if (!is3d) return;
    if (config.algorithms.length === 1 && config.algorithms[0] === "lazy-3d-astar") return;
    patch({ algorithms: ["lazy-3d-astar"], algorithmMode: "run-all" });
  }, [is3d, config.algorithms, patch]);
  const toggle = (algo: string) => {
    const has = config.algorithms.includes(algo);
    patch({
      algorithms: has ? config.algorithms.filter((a) => a !== algo) : [...config.algorithms, algo],
    });
  };
  return (
    <div className="stack">
      <div className="field-hint">
        {is3d
          ? "3D mode uses Lazy 3D A* only, so the algorithm preview is fixed."
          : "Select the algorithms you want to include in the run preview and backend request."}
      </div>
      {is3d ? (
        <div className="checkbox-group">
          <span className="chip">Lazy 3D A*</span>
        </div>
      ) : (
        <div className="checkbox-group">
          {options.map((algo) => (
            <label key={algo}>
              <input
                type="checkbox"
                checked={config.algorithms.includes(algo)}
                onChange={() => toggle(algo)}
              />
              {algo}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------ Sensors ------ */

function SensorsTab() {
  const { config, patch, issues } = useScenario();
  const mode = config.sensorMode;

  return (
    <div className="stack">
      <label>Sensor Definition Mode</label>
      <div className="mode-select">
        {(
          [
            [
              "auto",
              "Auto-generate sensors",
              "System places sensors using the selected placement strategy.",
            ],
            [
              "manual-counts",
              "Manually define sensor counts by type",
              "Specify per-type counts; system places them.",
            ],
            [
              "manual-table",
              "Manually enter full sensor data",
              "Editable table with id, type, coordinates, class.",
            ],
            [
              "uploaded",
              "Upload sensor CSV",
              "Upload sensor.csv — requires backend upload support.",
            ],
            ["pasted", "Paste sensor CSV text", "Paste CSV; parsed and validated in the browser."],
          ] as const
        ).map(([val, label, desc]) => (
          <label key={val} className={mode === val ? "selected" : ""}>
            <input
              type="radio"
              name="sensorMode"
              checked={mode === val}
              onChange={() => patch({ sensorMode: val })}
            />
            <span>
              <strong>{label}</strong>
              <span className="mode-desc">{desc}</span>
            </span>
          </label>
        ))}
      </div>

      {mode === "auto" && (
        <div className="form-grid">
          <div>
            <label htmlFor="sensorCount">Total sensor count</label>
            <input
              id="sensorCount"
              type="number"
              min={0}
              max={1000}
              step={1}
              value={config.sensorCount}
              onChange={(e) => patch({ sensorCount: parseInt(e.target.value || "0", 10) })}
            />
            {errorFor(issues, "sensorCount") ? (
              <div className="field-error">{errorFor(issues, "sensorCount")}</div>
            ) : (
              <div className="field-hint">Integer 0–1000.</div>
            )}
          </div>
          <div>
            <label htmlFor="placementMode">Placement mode</label>
            <select
              id="placementMode"
              value={config.placementMode}
              onChange={(e) =>
                patch({ placementMode: e.target.value as typeof config.placementMode })
              }
            >
              {PLACEMENT_MODES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {mode === "manual-counts" && <ManualCounts />}
      {mode === "manual-table" && <ManualSensorTable />}
      {mode === "uploaded" && <UploadCard label="sensor.csv" />}
      {mode === "pasted" && <PastedSensorCsv />}
    </div>
  );
}

function ManualCounts() {
  const { config, patch, issues } = useScenario();
  const c = config.sensorCounts;
  const total = c.radar + c.ir + c.acoustic + c.visual;
  const set = (k: keyof typeof c, v: number) => patch({ sensorCounts: { ...c, [k]: v } });
  return (
    <div>
      <div className="form-grid">
        {(["radar", "ir", "acoustic", "visual"] as const).map((k) => (
          <div key={k}>
            <label htmlFor={`sc-${k}`}>{k === "ir" ? "Infrared" : k} sensors</label>
            <input
              id={`sc-${k}`}
              type="number"
              min={0}
              step={1}
              value={c[k]}
              onChange={(e) => set(k, parseInt(e.target.value || "0", 10))}
            />
            {errorFor(issues, `sensorCounts.${k}`) && (
              <div className="field-error">{errorFor(issues, `sensorCounts.${k}`)}</div>
            )}
          </div>
        ))}
        <div>
          <label htmlFor="pm2">Placement mode</label>
          <select
            id="pm2"
            value={config.placementMode}
            onChange={(e) =>
              patch({ placementMode: e.target.value as typeof config.placementMode })
            }
          >
            {PLACEMENT_MODES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="readonly-list" style={{ marginTop: 12 }}>
        <dt>Total sensors</dt>
        <dd>{total}</dd>
      </div>
      {errorFor(issues, "sensorCounts") && (
        <div className="field-error">{errorFor(issues, "sensorCounts")}</div>
      )}
    </div>
  );
}

function ManualSensorTable() {
  const { config, patch, issues } = useScenario();
  const rows = config.manualSensors;
  const setRows = (rs: SensorRow[]) => patch({ manualSensors: rs });
  const add = () =>
    setRows([
      ...rows,
      {
        id: `s${rows.length + 1}`,
        sensor_type: "radar",
        label: "",
        x: 0,
        y: 0,
        z: 0,
        class: "static",
      },
    ]);
  const del = (i: number) => setRows(rows.filter((_, j) => j !== i));
  const dup = (i: number) =>
    setRows([
      ...rows.slice(0, i + 1),
      { ...rows[i], id: `${rows[i].id}_copy` },
      ...rows.slice(i + 1),
    ]);
  const clear = () => setRows([]);
  const update = (i: number, p: Partial<SensorRow>) =>
    setRows(rows.map((r, j) => (j === i ? { ...r, ...p } : r)));

  const [csvText, setCsvText] = useState("");
  const importCsv = () => {
    const { rows: rr } = csvToObjects(csvText);
    const parsed: SensorRow[] = rr.map((r, i) => ({
      id: r.id || `s${i + 1}`,
      sensor_type: (r.sensor_type || "radar") as SensorRow["sensor_type"],
      label: r.label || "",
      x: parseInt(r.x || "0", 10),
      y: parseInt(r.y || "0", 10),
      z: parseInt(r.z || "0", 10),
      class: r.class || "static",
    }));
    setRows(parsed);
    setCsvText("");
  };
  const exportCsv = () => {
    const csv = objectsToCsv(
      ["id", "sensor_type", "label", "x", "y", "z", "class"],
      rows as unknown as Record<string, unknown>[],
    );
    setCsvText(csv);
  };

  return (
    <div className="stack">
      <div className="row">
        <button className="btn btn-sm" onClick={add}>
          Add row
        </button>
        <button className="btn btn-sm" onClick={clear} disabled={!rows.length}>
          Clear table
        </button>
        <button className="btn btn-sm" onClick={exportCsv} disabled={!rows.length}>
          Export as CSV preview
        </button>
      </div>
      <div className="table-wrap compact">
        <table className="table">
          <thead>
            <tr>
              <th>id</th>
              <th>type</th>
              <th>label</th>
              <th className="num">x</th>
              <th className="num">y</th>
              <th className="num">z</th>
              <th>class</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={8} style={{ padding: 16, color: "var(--color-text-muted)" }}>
                  No rows. Use “Add row” or import from CSV below.
                </td>
              </tr>
            )}
            {rows.map((r, i) => (
              <tr key={i}>
                <td>
                  <input value={r.id} onChange={(e) => update(i, { id: e.target.value })} />
                </td>
                <td>
                  <select
                    value={r.sensor_type}
                    onChange={(e) =>
                      update(i, { sensor_type: e.target.value as SensorRow["sensor_type"] })
                    }
                  >
                    {["radar", "ir", "acoustic", "visual"].map((t) => (
                      <option key={t}>{t === "ir" ? "Infrared" : t}</option>
                    ))}
                  </select>
                </td>
                <td>
                  <input value={r.label} onChange={(e) => update(i, { label: e.target.value })} />
                </td>
                <td className="num">
                  <input
                    type="number"
                    min={0}
                    max={99}
                    value={r.x}
                    onChange={(e) => update(i, { x: parseInt(e.target.value || "0", 10) })}
                  />
                </td>
                <td className="num">
                  <input
                    type="number"
                    min={0}
                    max={99}
                    value={r.y}
                    onChange={(e) => update(i, { y: parseInt(e.target.value || "0", 10) })}
                  />
                </td>
                <td className="num">
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={r.z}
                    onChange={(e) => update(i, { z: parseInt(e.target.value || "0", 10) })}
                  />
                </td>
                <td>
                  <input value={r.class} onChange={(e) => update(i, { class: e.target.value })} />
                </td>
                <td style={{ whiteSpace: "nowrap" }}>
                  <button className="btn btn-sm" onClick={() => dup(i)}>
                    Dup
                  </button>{" "}
                  <button className="btn btn-sm btn-danger" onClick={() => del(i)}>
                    Del
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {issues
        .filter((i) => i.field.startsWith("manualSensors"))
        .slice(0, 5)
        .map((i, k) => (
          <div key={k} className="field-error">
            {i.message}
          </div>
        ))}
      <div>
        <label htmlFor="csvImport">Import / preview CSV (id,sensor_type,label,x,y,z,class)</label>
        <textarea
          id="csvImport"
          className="csv"
          value={csvText}
          onChange={(e) => setCsvText(e.target.value)}
        />
        <div className="field-hint">{CSV_WARNING_TEXT}</div>
        <div className="row" style={{ marginTop: 6 }}>
          <button className="btn btn-sm" onClick={importCsv} disabled={!csvText.trim()}>
            Use parsed data
          </button>
        </div>
      </div>
    </div>
  );
}

function PastedSensorCsv() {
  const { config, patch } = useScenario();
  const [csvText, setCsvText] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const parse = () => {
    try {
      const { header, rows } = csvToObjects(csvText);
      const required = ["id", "sensor_type", "label", "x", "y", "z", "class"];
      const missing = required.filter((r) => !header.includes(r));
      if (missing.length) {
        setParseError(`Missing columns: ${missing.join(", ")}`);
        return;
      }
      const parsed: SensorRow[] = rows.map((r, i) => ({
        id: r.id || `s${i + 1}`,
        sensor_type: (r.sensor_type || "radar") as SensorRow["sensor_type"],
        label: r.label || "",
        x: parseInt(r.x || "0", 10),
        y: parseInt(r.y || "0", 10),
        z: parseInt(r.z || "0", 10),
        class: r.class || "static",
      }));
      patch({ sensorMode: "manual-table", manualSensors: parsed });
      setParseError(null);
    } catch (e) {
      setParseError((e as Error).message);
    }
  };
  const counts = config.manualSensors.reduce<Record<string, number>>((a, s) => {
    a[s.sensor_type] = (a[s.sensor_type] || 0) + 1;
    return a;
  }, {});
  return (
    <div className="stack">
      <label htmlFor="pastedSensor">CSV text (id,sensor_type,label,x,y,z,class)</label>
      <textarea
        id="pastedSensor"
        className="csv"
        value={csvText}
        onChange={(e) => setCsvText(e.target.value)}
      />
      <div className="field-hint">{CSV_WARNING_TEXT}</div>
      <div className="row">
        <button className="btn btn-sm" onClick={parse} disabled={!csvText.trim()}>
          Parse CSV
        </button>
        <button
          className="btn btn-sm"
          onClick={() => {
            setCsvText("");
            setParseError(null);
          }}
        >
          Clear
        </button>
      </div>
      {parseError && <div className="alert alert-error">{parseError}</div>}
      {config.manualSensors.length > 0 && (
        <div className="readonly-list">
          <dt>Parsed rows</dt>
          <dd>{config.manualSensors.length}</dd>
          {["radar", "ir", "acoustic", "visual"].map((t) => (
            <>
              <dt key={`k${t}`}>{t === "ir" ? "Infrared" : t}</dt>
              <dd key={`v${t}`}>{counts[t] ?? 0}</dd>
            </>
          ))}
        </div>
      )}
    </div>
  );
}

function UploadCard({ label }: { label: string }) {
  const [status, setStatus] = useState<"idle" | "chosen">("idle");
  const [name, setName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="panel" style={{ margin: 0 }}>
      <div className="panel-header">{label}</div>
      <div className="panel-body stack">
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => {
            const f = e.target.files?.[0];
            setError(null);
            if (!f) {
              setName("");
              setStatus("idle");
              return;
            }
            const lowerName = f.name.toLowerCase();
            const allowedMime =
              f.type === "" || f.type === "text/csv" || f.type === "application/vnd.ms-excel";
            if (!lowerName.endsWith(".csv")) {
              setError("Only .csv files are accepted.");
              setName("");
              setStatus("idle");
              return;
            }
            if (!allowedMime) {
              setError("This file does not look like a CSV.");
              setName("");
              setStatus("idle");
              return;
            }
            if (f.size > MAX_CSV_FILE_SIZE_BYTES) {
              setError("CSV files must be 5 MB or smaller.");
              setName("");
              setStatus("idle");
              return;
            }
            setName(f.name);
            setStatus("chosen");
          }}
        />
        <div className="readonly-list">
          <dt>Status</dt>
          <dd>{status === "idle" ? "Not uploaded" : `Selected: ${name}`}</dd>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <div className="field-hint">{CSV_WARNING_TEXT}</div>
        <div className="alert alert-warn">
          Backend upload support required. The file is not sent until the backend exposes a
          multipart upload endpoint. Submitting will be blocked in this mode.
        </div>
      </div>
    </div>
  );
}

/* ------ UAV ------ */

function UavTab() {
  const { config, patch } = useScenario();
  const d = DRONE_BY_NAME[config.droneName];
  return (
    <div className="stack">
      <div className="form-grid">
        <div>
          <label htmlFor="drone">Drone</label>
          <select
            id="drone"
            value={config.droneName}
            onChange={(e) => patch({ droneName: e.target.value })}
          >
            {DRONE_NAMES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <div className="field-hint">
            Selected UAV parameters affect threat probability and cost-field evaluation.
          </div>
        </div>
      </div>
      {d && (
        <div
          className="readonly-list"
          style={{ gridTemplateColumns: "max-content 1fr max-content 1fr" }}
        >
          <dt>UAV class</dt>
          <dd>{d.uav_class}</dd>
          <dt>Propulsion</dt>
          <dd>{d.propulsion_class}</dd>
          <dt>Max speed</dt>
          <dd>{d.max_speed} m/s</dd>
          <dt>Ceiling</dt>
          <dd>{d.ceiling} m</dd>
          <dt>MTOW</dt>
          <dd>{d.mtow} kg</dd>
          <dt>Wingspan</dt>
          <dd>{d.wingspan} m</dd>
          <dt>Length</dt>
          <dd>{d.length} m</dd>
          <dt>Wing area</dt>
          <dd>{d.wing_area} m²</dd>
          <dt>Stall speed</dt>
          <dd>{d.stall_speed} m/s</dd>
          <dt>Max wind tolerance</dt>
          <dd>{d.max_wind_tolerance} m/s</dd>
          <dt>Failure probability</dt>
          <dd>{d.failure_probability}</dd>
        </div>
      )}
    </div>
  );
}

/* ------ Input Mode ------ */

function InputModeTab() {
  const { config, patch } = useScenario();
  return (
    <div className="stack">
      <label>Input mode</label>
      <div className="mode-select">
        {(
          [
            [
              "generated",
              "Generate scenario automatically",
              "Backend generates terrain, sensors, NFZ, and env from the seed.",
            ],
            [
              "uploaded",
              "Upload CSV files",
              "Provide terrain_height / terrain_type / sensor / nfz / env — requires backend upload support.",
            ],
            ["pasted", "Paste CSV data manually", "Paste CSVs into the textareas below."],
            ["hybrid", "Hybrid mode", "Choose the source per input file."],
          ] as const
        ).map(([val, label, desc]) => (
          <label key={val} className={config.inputMode === val ? "selected" : ""}>
            <input
              type="radio"
              name="inputMode"
              checked={config.inputMode === val}
              onChange={() => patch({ inputMode: val })}
            />
            <span>
              <strong>{label}</strong>
              <span className="mode-desc">{desc}</span>
            </span>
          </label>
        ))}
      </div>

      {config.inputMode === "generated" && (
        <div className="alert alert-info">
          All input files (terrain_height.csv, terrain_type.csv, sensor.csv, nfz.csv, env.csv) will
          be generated by the backend from the configured seed and threat/sensor settings.
        </div>
      )}
      {config.inputMode === "uploaded" && (
        <>
          <div className="alert alert-warn">
            Backend upload support required. Uploads are not yet transmitted; Run Simulation is
            blocked in this mode.
          </div>
          <div className="form-grid">
            {(["terrain_height", "terrain_type", "sensor", "nfz", "env"] as const).map((k) => (
              <UploadCard key={k} label={`${k}.csv`} />
            ))}
          </div>
        </>
      )}
      {config.inputMode === "pasted" && (
        <div className="stack">
          {(["terrain_height", "terrain_type", "sensor", "nfz", "env"] as const).map((k) => (
            <PastedCsvBox key={k} name={`${k}.csv`} />
          ))}
        </div>
      )}
      {config.inputMode === "hybrid" && <HybridSourceTable />}
    </div>
  );
}

function PastedCsvBox({ name }: { name: string }) {
  const [text, setText] = useState("");
  const [rows, setRows] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const parse = () => {
    try {
      const r = csvToObjects(text);
      setRows(r.rows.length);
      setErr(null);
    } catch (e) {
      setErr((e as Error).message);
    }
  };
  return (
    <div className="panel" style={{ margin: 0 }}>
      <div className="panel-header">{name}</div>
      <div className="panel-body stack">
        <textarea className="csv" value={text} onChange={(e) => setText(e.target.value)} />
        <div className="field-hint">{CSV_WARNING_TEXT}</div>
        <div className="row">
          <button className="btn btn-sm" onClick={parse} disabled={!text.trim()}>
            Parse
          </button>
          <button
            className="btn btn-sm"
            onClick={() => {
              setText("");
              setRows(null);
              setErr(null);
            }}
          >
            Clear
          </button>
        </div>
        {err && <div className="alert alert-error">{err}</div>}
        {rows !== null && (
          <div className="readonly-list">
            <dt>Data rows</dt>
            <dd>{rows}</dd>
          </div>
        )}
        <div className="alert alert-warn">
          Backend upload/paste support required. This preview validates locally but is not yet
          transmitted.
        </div>
      </div>
    </div>
  );
}

function HybridSourceTable() {
  const { config, patch } = useScenario();
  const files = [
    { key: "terrain_height", options: ["generated", "uploaded", "pasted"] },
    { key: "terrain_type", options: ["generated", "uploaded", "pasted"] },
    { key: "sensor", options: ["generated", "manual-table", "uploaded", "pasted"] },
    { key: "nfz", options: ["generated", "uploaded", "pasted"] },
    { key: "env", options: ["generated", "uploaded", "pasted"] },
  ] as const;
  const set = (k: string, v: string) =>
    patch({ inputSources: { ...config.inputSources, [k]: v as never } });
  return (
    <>
      <table className="table">
        <thead>
          <tr>
            <th>File</th>
            <th>Source</th>
            <th>Status</th>
            <th>Preview</th>
          </tr>
        </thead>
        <tbody>
          {files.map((f) => {
            const cur = (config.inputSources as Record<string, string>)[f.key];
            return (
              <tr key={f.key}>
                <td className="mono">{f.key}.csv</td>
                <td>
                  <select value={cur} onChange={(e) => set(f.key, e.target.value)}>
                    {f.options.map((o) => (
                      <option key={o} value={o}>
                        {o}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  {cur === "generated"
                    ? "Auto (backend)"
                    : "User-provided — backend support required"}
                </td>
                <td style={{ color: "var(--color-text-muted)" }}>—</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="alert alert-warn" style={{ marginTop: 12 }}>
        Any file not set to “generated” requires backend upload support. Run Simulation is blocked
        until every non-generated file has a supported delivery path.
      </div>
    </>
  );
}

/* ------ Review ------ */

interface ReviewProps {
  issues: ValidationIssue[];
  reviewVisited: boolean;
  confirmed: boolean;
  onConfirm: (v: boolean) => void;
  canRun: boolean;
  onRun: () => void;
  onReset: () => void;
  submitting: boolean;
  uploadUnavailable: boolean;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel" style={{ margin: 0 }}>
      <div className="panel-header">{title}</div>
      <div className="panel-body">{children}</div>
    </section>
  );
}

function ReviewTab({
  issues,
  reviewVisited,
  confirmed,
  onConfirm,
  canRun,
  onRun,
  onReset,
  submitting,
  uploadUnavailable,
}: ReviewProps) {
  const { config } = useScenario();
  const d = DRONE_BY_NAME[config.droneName];
  const dist = useMemo(() => {
    const { start, end } = config.route;
    return Math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2);
  }, [config.route]);
  const blocking = issues.filter((i) => i.blocking);

  const totalSensors =
    config.sensorMode === "auto"
      ? config.sensorCount
      : config.sensorMode === "manual-counts"
        ? config.sensorCounts.radar +
          config.sensorCounts.ir +
          config.sensorCounts.acoustic +
          config.sensorCounts.visual
        : config.manualSensors.length;

  return (
    <div className="stack">
      <Section title="Mission Summary">
        <dl className="summary-grid">
          <dt>Grid</dt>
          <dd>100 × 100 (1 km / cell)</dd>
          <dt>Z scale</dt>
          <dd>100 m / z unit</dd>
          <dt>Flight altitude</dt>
          <dd>{config.flightZ}</dd>
        </dl>
      </Section>
      <Section title="Route Summary">
        <dl className="summary-grid">
          <dt>Start</dt>
          <dd>
            ({config.route.start.x}, {config.route.start.y}, {config.route.start.z})
          </dd>
          <dt>End</dt>
          <dd>
            ({config.route.end.x}, {config.route.end.y}, {config.route.end.z})
          </dd>
          <dt>Distance</dt>
          <dd>
            {dist.toFixed(2)} cells ≈ {dist.toFixed(2)} km
          </dd>
        </dl>
      </Section>
      <Section title="Terrain Summary">
        <dl className="summary-grid">
          <dt>Source</dt>
          <dd>{config.inputSources.terrain_height}</dd>
          <dt>Seed</dt>
          <dd>{config.terrainSeed}</dd>
        </dl>
      </Section>
      <Section title="Threat Summary">
        <dl className="summary-grid">
          <dt>Threat types</dt>
          <dd>{config.threatTypes.join(", ") || "—"}</dd>
          <dt>NFZ count</dt>
          <dd>{config.nfzCount}</dd>
          <dt>NFZ source</dt>
          <dd>{config.inputSources.nfz}</dd>
        </dl>
      </Section>
      <Section title="Sensor Summary">
        <dl className="summary-grid">
          <dt>Mode</dt>
          <dd>{config.sensorMode}</dd>
          <dt>Total</dt>
          <dd>{totalSensors}</dd>
          {config.sensorMode === "auto" && (
            <>
              <dt>Placement</dt>
              <dd>{config.placementMode}</dd>
            </>
          )}
          {config.sensorMode === "manual-counts" && (
            <>
              <dt>Radar</dt>
              <dd>{config.sensorCounts.radar}</dd>
              <dt>Infrared</dt>
              <dd>{config.sensorCounts.ir}</dd>
              <dt>Acoustic</dt>
              <dd>{config.sensorCounts.acoustic}</dd>
              <dt>Visual</dt>
              <dd>{config.sensorCounts.visual}</dd>
            </>
          )}
        </dl>
      </Section>
      <Section title="UAV Summary">
        {d && (
          <dl className="summary-grid">
            <dt>Drone</dt>
            <dd>{d.name}</dd>
            <dt>Class</dt>
            <dd>{d.uav_class}</dd>
            <dt>Propulsion</dt>
            <dd>{d.propulsion_class}</dd>
            <dt>Max speed</dt>
            <dd>{d.max_speed} m/s</dd>
            <dt>Ceiling</dt>
            <dd>{d.ceiling} m</dd>
            <dt>MTOW</dt>
            <dd>{d.mtow} kg</dd>
          </dl>
        )}
      </Section>
      <Section title="Algorithm Preview">
        <div className="field-hint" style={{ marginBottom: 10 }}>
          The selected algorithms are shown here as a run plan only. Visualization remains disabled
          for now.
        </div>
        <div className="checkbox-group">
          {config.algorithms.map((algo) => (
            <span key={algo} className="chip">
              {algo}
            </span>
          ))}
        </div>
      </Section>
      <Section title="Validation Status">
        {blocking.length === 0 ? (
          <div className="badge badge-completed">Ready to run</div>
        ) : (
          <>
            <div className="badge badge-failed" style={{ marginBottom: 8 }}>
              Blocking errors: {blocking.length}
            </div>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {blocking.map((b, i) => (
                <li key={i}>
                  <span className="mono">{b.field}</span> — {b.message}
                </li>
              ))}
            </ul>
          </>
        )}
        {uploadUnavailable && (
          <div className="alert alert-warn" style={{ marginTop: 10 }}>
            Backend upload / paste transmission support required for the selected input mode. Run
            Simulation is available but the backend may reject files it does not receive.
          </div>
        )}
      </Section>

      <div
        className="actions-bar"
        style={{
          borderTop: "1px solid var(--color-border)",
          background: "var(--color-surface)",
          marginTop: 12,
        }}
      >
        <label
          style={{
            marginRight: "auto",
            textTransform: "none",
            fontWeight: 500,
            fontSize: 13,
            color: "var(--color-text)",
            letterSpacing: 0,
          }}
        >
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => onConfirm(e.target.checked)}
            disabled={blocking.length > 0}
          />
          I have reviewed the scenario configuration.
        </label>
        <button className="btn" onClick={onReset} disabled={submitting}>
          Reset
        </button>
        <button className="btn btn-primary" onClick={onRun} disabled={!canRun}>
          {submitting ? "Submitting…" : "Run Simulation"}
        </button>
      </div>
      {!reviewVisited && (
        <div className="field-hint">
          Visit the Review tab before enabling the confirmation checkbox.
        </div>
      )}
    </div>
  );
}
