const fs = require("fs/promises");
const path = require("path");
const { safeResolveRunFolder } = require("./runDiscovery.service");

const SAFE_FILENAME = /^[A-Za-z0-9_.-]+$/;
const ARTIFACT_CACHE_TTL_MS = 5000;
const artifactCache = new Map();

function labelForFile(filename) {
  const name = filename.replace(/\.[^.]+$/, "");
  if (filename.endsWith(".csv")) {
    const map = {
      terrain_height: "Terrain Height",
      terrain_type: "Terrain Type",
      sensor: "Sensors CSV",
      nfz: "NFZ CSV",
      env: "Environment CSV",
      final_cost: "Final Cost CSV",
      algorithm_metrics: filename.endsWith(".json") ? "Algorithm Metrics JSON" : "Algorithm Metrics CSV"
    };
    return map[name] || titleCase(name);
  }
  if (filename.includes("terrain")) return "Terrain";
  if (filename.includes("sensor")) return "Sensors";
  if (filename.includes("final") || filename.includes("cost")) return "Final Cost";
  return titleCase(name);
}

async function discoverArtifacts(runId) {
  const runDir = safeResolveRunFolder(runId);
  const cached = artifactCache.get(runId);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.value;
  }
  const csv = await listFiles(runId, path.join(runDir, "csv"), [".csv", ".json"], "files");
  const outputs = await listFiles(runId, path.join(runDir, "outputs"), [".csv", ".json"], "files");
  const plots = await listFiles(runId, path.join(runDir, "plots"), [".png"], "plots");
  const value = { runId, available: true, csv, outputs, plots };
  artifactCache.set(runId, { expiresAt: Date.now() + ARTIFACT_CACHE_TTL_MS, value });
  return value;
}

async function listFiles(runId, dir, extensions, kind) {
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    return entries
      .filter((e) => e.isFile() && !e.name.startsWith(".") && SAFE_FILENAME.test(e.name))
      .filter((e) => extensions.some((ext) => e.name.endsWith(ext)))
      .map((e) => ({
        filename: e.name,
        url: `/api/runs/${encodeURIComponent(runId)}/${kind}/${encodeURIComponent(e.name)}`,
        label: labelForFile(e.name)
      }));
  } catch {
    return [];
  }
}

function titleCase(value) {
  return value
    .split(/[_\-. ]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

module.exports = { discoverArtifacts };
