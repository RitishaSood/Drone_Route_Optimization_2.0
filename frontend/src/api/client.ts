const RUN_ID_PATTERN = /^[A-Za-z0-9_-]{1,100}$/;

export const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || "/api";

export const ALLOWED_PLOT_FILENAMES = [
  "terrain.png",
  "terrain_3d.png",
  "sensors.png",
  "suitability.png",
  "layers.png",
  "final_cost_heatmap.png",
  "final_cost_binary.png",
] as const;

export const ALLOWED_FILE_FILENAMES = [
  "terrain_height.csv",
  "terrain_type.csv",
  "sensor.csv",
  "nfz.csv",
  "env.csv",
  "final_cost.csv",
] as const;

export type AllowedPlotFilename = (typeof ALLOWED_PLOT_FILENAMES)[number];
export type AllowedFileFilename = (typeof ALLOWED_FILE_FILENAMES)[number];

function normalizeBase(base: string) {
  if (base === "/api") return base;
  return base.replace(/\/+$/, "");
}

function assertRunId(runId: string) {
  if (!RUN_ID_PATTERN.test(runId)) {
    throw new Error("Invalid run ID.");
  }
}

function assertAllowedFilename<T extends readonly string[]>(filename: string, allowlist: T) {
  if (!allowlist.includes(filename as T[number])) {
    throw new Error("Invalid file requested.");
  }
}

function buildUrl(path: string) {
  if (normalizeBase(API_BASE) === "/api") {
    return path;
  }

  return `${normalizeBase(API_BASE)}${path}`;
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(buildUrl(path), {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return (await res.json()) as T;
}

export async function apiFetch(path: string, init?: RequestInit) {
  return fetch(buildUrl(path), init);
}

export function buildPlotUrl(runId: string, filename: AllowedPlotFilename) {
  assertRunId(runId);
  assertAllowedFilename(filename, ALLOWED_PLOT_FILENAMES);
  return buildUrl(`/api/runs/${encodeURIComponent(runId)}/plots/${encodeURIComponent(filename)}`);
}

export function buildFileUrl(runId: string, filename: AllowedFileFilename) {
  assertRunId(runId);
  assertAllowedFilename(filename, ALLOWED_FILE_FILENAMES);
  return buildUrl(`/api/runs/${encodeURIComponent(runId)}/files/${encodeURIComponent(filename)}`);
}

export { RUN_ID_PATTERN };
