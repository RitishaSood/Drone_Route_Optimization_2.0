import {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
  type ReactNode,
} from "react";
import type { ScenarioConfig, SensorRow } from "@/lib/uav-api";

const CLIENT_ID_KEY = "uav.clientId";

export const DEFAULT_CONFIG: ScenarioConfig = {
  flightZ: 50,
  route: { start: { x: 0, y: 0, z: 50 }, end: { x: 99, y: 99, z: 50 } },
  terrainSeed: 42,
  threatTypes: ["radar", "ir", "visual"],
  nfzCount: 3,
  sensorMode: "auto",
  sensorCount: 20,
  sensorCounts: { radar: 0, ir: 0, acoustic: 0, visual: 0 },
  manualSensors: [],
  inputMode: "generated",
  inputSources: {
    terrain_height: "generated",
    terrain_type: "generated",
    sensor: "generated",
    nfz: "generated",
    env: "generated",
  },
  droneName: "IAI Heron",
  placementMode: "greedy",
  algorithmMode: "run-all",
  algorithms: ["dijkstra", "astar", "ant-colony", "theta-star", "dstar-lite"],
};

export interface ValidationIssue { field: string; message: string; blocking: boolean }

export function validateScenario(cfg: ScenarioConfig): ValidationIssue[] {
  const errs: ValidationIssue[] = [];
  const intIn = (n: number, min: number, max: number) =>
    Number.isInteger(n) && n >= min && n <= max;

  if (!intIn(cfg.flightZ, 0, 100))
    errs.push({ field: "flightZ", message: "Flight altitude must be an integer 0–100.", blocking: true });
  if (!intIn(cfg.route.start.x, 0, 99))
    errs.push({ field: "route.start.x", message: "Start X must be 0–99.", blocking: true });
  if (!intIn(cfg.route.start.y, 0, 99))
    errs.push({ field: "route.start.y", message: "Start Y must be 0–99.", blocking: true });
  if (!intIn(cfg.route.end.x, 0, 99))
    errs.push({ field: "route.end.x", message: "End X must be 0–99.", blocking: true });
  if (!intIn(cfg.route.end.y, 0, 99))
    errs.push({ field: "route.end.y", message: "End Y must be 0–99.", blocking: true });
  if (cfg.route.start.x === cfg.route.end.x && cfg.route.start.y === cfg.route.end.y)
    errs.push({ field: "route", message: "Start and end points cannot be identical.", blocking: true });

  if (!intIn(cfg.terrainSeed, 0, 2147483647))
    errs.push({ field: "terrainSeed", message: "Terrain seed must be an integer 0–2,147,483,647.", blocking: true });

  if (cfg.threatTypes.length === 0)
    errs.push({ field: "threatTypes", message: "Select at least one threat type.", blocking: true });
  if (!intIn(cfg.nfzCount, 0, 100))
    errs.push({ field: "nfzCount", message: "NFZ count must be an integer 0–100.", blocking: true });

  if (cfg.sensorMode === "auto") {
    if (!intIn(cfg.sensorCount, 0, 1000))
      errs.push({ field: "sensorCount", message: "Sensor count must be 0–1000.", blocking: true });
  } else if (cfg.sensorMode === "manual-counts") {
    const c = cfg.sensorCounts;
    const total = c.radar + c.ir + c.acoustic + c.visual;
    (["radar", "ir", "acoustic", "visual"] as const).forEach((k) => {
      if (!Number.isInteger(c[k]) || c[k] < 0)
        errs.push({ field: `sensorCounts.${k}`, message: `${k} sensor count must be a non-negative integer.`, blocking: true });
    });
    if (total > 1000)
      errs.push({ field: "sensorCounts", message: "Total sensor count must be ≤ 1000.", blocking: true });
  } else if (cfg.sensorMode === "manual-table") {
    if (cfg.manualSensors.length === 0)
      errs.push({ field: "manualSensors", message: "Add at least one sensor row or switch mode.", blocking: true });
    const ids = new Set<string>();
    cfg.manualSensors.forEach((s, i) => {
      if (!s.id) errs.push({ field: `manualSensors[${i}].id`, message: `Row ${i + 1}: id required.`, blocking: true });
      else if (ids.has(s.id)) errs.push({ field: `manualSensors[${i}].id`, message: `Row ${i + 1}: duplicate id "${s.id}".`, blocking: true });
      else ids.add(s.id);
      if (!s.sensor_type) errs.push({ field: `manualSensors[${i}].sensor_type`, message: `Row ${i + 1}: sensor_type required.`, blocking: true });
      if (!intIn(s.x, 0, 99)) errs.push({ field: `manualSensors[${i}].x`, message: `Row ${i + 1}: x must be 0–99.`, blocking: true });
      if (!intIn(s.y, 0, 99)) errs.push({ field: `manualSensors[${i}].y`, message: `Row ${i + 1}: y must be 0–99.`, blocking: true });
      if (!intIn(s.z, 0, 100)) errs.push({ field: `manualSensors[${i}].z`, message: `Row ${i + 1}: z must be 0–100.`, blocking: true });
      if (!s.class) errs.push({ field: `manualSensors[${i}].class`, message: `Row ${i + 1}: class required.`, blocking: true });
    });
  }

  return errs;
}

interface ScenarioCtx {
  clientId: string;
  config: ScenarioConfig;
  setConfig: (c: ScenarioConfig) => void;
  patch: (p: Partial<ScenarioConfig>) => void;
  reset: () => void;
  issues: ValidationIssue[];
  reviewVisited: boolean;
  markReviewVisited: () => void;
  confirmed: boolean;
  setConfirmed: (v: boolean) => void;
}

const Ctx = createContext<ScenarioCtx | null>(null);

export function ScenarioProvider({ children }: { children: ReactNode }) {
  const [clientId, setClientId] = useState<string>("");
  const [config, setConfigState] = useState<ScenarioConfig>(DEFAULT_CONFIG);
  const [reviewVisited, setReviewVisited] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    let v = window.localStorage.getItem(CLIENT_ID_KEY);
    if (!v) {
      v = crypto.randomUUID();
      window.localStorage.setItem(CLIENT_ID_KEY, v);
    }
    setClientId(v);
  }, []);

  const setConfig = useCallback((c: ScenarioConfig) => {
    setConfigState(c);
  }, []);
  const patch = useCallback((p: Partial<ScenarioConfig>) => {
    setConfigState((c) => {
      const next = { ...c, ...p };
      // keep route z synced to flightZ
      if (p.flightZ !== undefined) {
        next.route = {
          start: { ...next.route.start, z: p.flightZ },
          end: { ...next.route.end, z: p.flightZ },
        };
      }
      return next;
    });
  }, []);
  const reset = useCallback(() => {
    setConfigState(DEFAULT_CONFIG);
    setReviewVisited(false);
    setConfirmed(false);
  }, []);
  const markReviewVisited = useCallback(() => {
    setReviewVisited(true);
  }, []);

  const issues = useMemo(() => validateScenario(config), [config]);

  const value = useMemo<ScenarioCtx>(
    () => ({
      clientId,
      config,
      setConfig,
      patch,
      reset,
      issues,
      reviewVisited,
      markReviewVisited,
      confirmed,
      setConfirmed,
    }),
    [
      clientId,
      config,
      setConfig,
      patch,
      reset,
      issues,
      reviewVisited,
      markReviewVisited,
      confirmed,
      setConfirmed,
    ],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useScenario(): ScenarioCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useScenario must be used within ScenarioProvider");
  return ctx;
}
