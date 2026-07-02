# UAV Route Optimization — Full Frontend Rebuild

Replace the current single-page UI with a four-page academic dashboard. Backend contracts stay as they are; features that need new backend endpoints render explicit "backend support required" states instead of faking success.

## Scope

- Wipe current dashboard UI in `src/routes/index.tsx`.
- Add multi-page routing, a shared top nav, and a strict black-and-white academic theme.
- Build the new Simulation Setup workflow, Results page, Drone Database, and Methodology page.
- Rework the API client and add persistent `clientId` + scenario state via React context.

## Pages & routes

Top nav (no sidebar): `UAV Route Optimization | Simulation | Results | Drone Database | Methodology`.

```
src/routes/
  __root.tsx           # shell + top nav + providers
  index.tsx            # redirects to /simulation
  simulation.tsx       # Page 1 — Simulation Setup
  results.tsx          # Page 2 — Run Results (list + detail)
  drones.tsx           # Page 3 — Drone Database
  methodology.tsx      # Page 4 — About / Methodology
```

Each route sets its own `head()` metadata (title + description).

## Visual system

- Global CSS in `src/styles.css`. Palette: pure black, white, and a small grayscale ramp (`--fg`, `--fg-muted`, `--border`, `--bg`, `--panel`, `--panel-alt`).
- No gradients, no glow, no glassmorphism, no rounded pills. Border-radius ≤ 2px. 1px solid borders on panels, tables, inputs.
- Typography: system serif for H1/H2 (`Georgia, "Times New Roman", serif`), system sans (`-apple-system, "Segoe UI", Roboto, sans-serif`) for body, monospace for IDs and numeric cells.
- Compact tables with sticky headers, zebra stripes in `#f5f5f5`, strong header rule.
- Focus states: 2px solid black outline. Status conveyed by text + shape, never color alone.

## Page 1 — Simulation Setup

Staged workflow shown as a numbered progress strip: **1. Configure → 2. Validate → 3. Preview → 4. Confirm & Run**. Configure hosts eight tabs: Mission, Route, Terrain, Threats, Sensors, UAV, Input Mode, Review.

Validation runs continuously via Zod schemas per tab; a compact validation panel is always visible. The single **Run Simulation** button lives at the bottom of Review and is disabled until:

1. No blocking errors across all tabs.
2. User has visited the Review tab at least once.
3. Confirmation checkbox "I have reviewed the scenario configuration." is checked.

Tab specifics follow the spec exactly:

- **Mission**: read-only grid facts + editable `flightZ` (int 0–100, default 50).
- **Route**: `startX/Y`, `endX/Y` (int 0–99, default 0,0 → 99,99); `startZ`/`endZ` shown read-only, derived from `flightZ`; start ≠ end.
- **Terrain**: `terrainSeed` (int 0–2147483647, default 42) + read-only terrain classes list.
- **Threats**: checkboxes for radar/ir/acoustic/visual (defaults: radar, ir, visual on); `nfzCount` int 0–100, default 3; at least one type required.
- **Sensors**: mode selector with five options — auto count + placement (greedy/random/strategic), manual counts by type, manual editable sensor table (add/delete/duplicate/clear/import from CSV/export), upload sensor CSV, paste sensor CSV. All parsing client-side via a small CSV parser; strict schema validation; preview shows row + per-type counts. CSV is only rendered into `<td>` text nodes — never HTML.
- **UAV**: dropdown of the 13 drones; compact static summary card (excludes speed/heading). Backing data lives in `src/data/drones.ts`.
- **Input Mode**: four modes — generated, upload files, paste CSV, hybrid. Hybrid shows a `File | Source | Status | Preview` table. Upload cards accept `.csv` only and show `Not uploaded / Uploaded / Parsed / Invalid`. If backend has no upload endpoint the submit path shows a blocking "Backend upload support required" message rather than pretending.
- **Review**: full scenario summary in sectioned panels (Mission, Route, Terrain, Threats, Sensors, UAV, Algorithm Execution Plan, Validation Status). Algorithms shown as fixed "run-all" list. Bottom bar: confirmation checkbox, Reset, Run Simulation.

## Page 2 — Run Results

Left column: recent runs table (id, status, created, duration). Selecting a row loads the detail view; polling continues for the active run.

Detail view sections:

1. **Current Run Summary** — ids, status, timestamps, duration, error text (plain).
2. **Scenario Summary** — echoes the submitted config.
3. **Algorithm Comparison** — table with columns `Algorithm | Status | Total Cost | Runtime | Nodes Visited | Path Nodes | Total Distance | Success`, sortable by cost/runtime/nodes/distance and filter "successful only". If metrics aren't provided by backend, show a single row per algorithm with em-dash placeholders and a note: "Algorithm comparison will appear after route-planning outputs are generated."
4. **Best Algorithm Summary** — best-by-cost/runtime/distance/overall, computed client-side from whatever metrics arrive.
5. **Plots** grouped as Environment / Threat Modeling / Final Cost / Path Outputs. Each plot fetched via `getPlotUrl`; missing plots render neutral "Not available" placeholders (no broken images).
6. **Downloads** — input CSVs, output CSVs, and per-algorithm CSVs; only rendered when backend reports the file exists (probe with HEAD on demand; fall back to hiding unresolved future files).

## Page 3 — Drone Database

- Data source: `src/data/drones.ts` (the 13 provided drones, verbatim).
- Static banner with the unit-caveat note.
- Toolbar: text search (name/class/propulsion), filter selects for UAV class and propulsion class, column visibility toggle popover.
- Table: sticky header, horizontal scroll, all columns from spec with labeled units; excludes speed/heading. Sortable columns as listed (name A–Z/Z–A; asc/desc for max speed, ceiling, MTOW, wingspan, length, wing area, stall speed, max wind tolerance, failure probability).
- Row click opens a right-side detail panel with grouped sections: Identity, Performance, Geometry, Radar / Signature, IR Model, Acoustic Model, Visual Model, Reliability. Fields `i_base`, `c_drag`, `s_idle`, `c_aero` are labeled "(model units)".

## Page 4 — Methodology

Concise ordered write-up of the pipeline (terrain → threat/sensor placement → threat probability → cost map → multi-algorithm planning → comparison). Plain prose, semantic headings, no marketing chrome.

## Shared code layout

```
src/
  routes/…                       # pages above
  components/
    nav/TopNav.tsx
    layout/PageShell.tsx
    layout/Panel.tsx
    setup/StepStrip.tsx
    setup/tabs/{Mission,Route,Terrain,Threats,Sensors,UAV,InputMode,Review}Tab.tsx
    setup/SensorTable.tsx
    setup/CsvUploadCard.tsx
    setup/CsvPasteBox.tsx
    results/RunList.tsx
    results/AlgorithmComparison.tsx
    results/PlotGrid.tsx
    results/DownloadList.tsx
    drones/DroneTable.tsx
    drones/DroneDetail.tsx
  state/
    ScenarioContext.tsx          # form state + validation + review-visited flag
    clientId.ts                  # localStorage-backed UUID
  data/drones.ts
  lib/
    api/client.ts                # thin fetch wrapper on VITE_API_BASE_URL
    csv/parse.ts                 # header-driven CSV → rows, plain-text only
    csv/validators.ts            # per-file schema checks (terrain, sensor, nfz, env)
    validation/scenario.ts       # Zod schemas per tab + aggregate
  styles.css                     # black-and-white tokens + base element styles
```

State is held in a `ScenarioContext` provider mounted in `__root.tsx`, alongside a `RunsContext` for the results page polling loop. No global store library.

## API client

`src/lib/api/client.ts` reads `import.meta.env.VITE_API_BASE_URL` (default `http://localhost:5000`) and exposes:

`createRun(payload)`, `getRuns(clientId)`, `getRun(runId)`, `getRunStatus(runId)`, `getPlotUrl(runId, filename)`, `getFileUrl(runId, filename)`, `getAlgorithmMetrics(runId)` (tries `/api/runs/:id/metrics`; returns `null` on 404 so the UI can render placeholders).

Run payload matches the spec exactly, including `route`, `sensorMode`, `sensorCounts`, `manualSensors`, `inputMode`, `inputSources`, `algorithmMode: "run-all"`, and the fixed `algorithms` array.

For uploaded/pasted CSV modes, the client attempts `multipart/form-data` to `/api/runs`; if the backend returns 4xx indicating unsupported upload, the UI surfaces "Backend upload support required" and blocks Run Simulation.

## Security & a11y guardrails

- No `dangerouslySetInnerHTML` anywhere. All CSV cells rendered as text.
- File `<input>` restricted to `accept=".csv,text/csv"`; MIME + extension checked client-side; backend is authoritative.
- Every input has an associated `<label>`; tabs use `role="tablist"` with arrow-key navigation; buttons have visible 2px focus rings; tables use `<th scope="col">`.
- Status labels always include text (e.g. "Failed", "Ready to run"), never color alone.

## Verification

After the rebuild:

1. `bun run build` (auto-run by harness) must succeed with the new route tree.
2. Drive Playwright against `http://localhost:8080/simulation` to confirm: tabs render, Run button is disabled until Review + checkbox, submitting posts the expected JSON to `${VITE_API_BASE_URL}/api/runs`, Results page renders placeholders when metrics/plots are missing, Drone Database sorts/filters/opens the detail panel.
3. Screenshot the four pages to confirm the black-and-white academic look.

## Out of scope

- Any backend/API changes.
- Real 3D route mode (space reserved in the Route tab but not implemented).
- Terrain distribution sliders (not exposed until backend supports them).
- Auth, persistence beyond `localStorage` clientId, or analytics.
