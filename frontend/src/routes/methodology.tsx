import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/methodology")({
  component: MethodologyPage,
});

function MethodologyPage() {
  return (
    <div className="page prose">
      <header className="app-header">
        <h1>About / Methodology</h1>
        <div className="subtitle">A concise description of the terrain-aware UAV route optimization pipeline.</div>
      </header>

      <section className="panel">
        <div className="panel-header">Pipeline Overview</div>
        <div className="panel-body">
          <p>
            The pipeline evaluates candidate UAV routes over a discrete 100 × 100 grid environment,
            where each cell corresponds to a 1 km × 1 km ground footprint and each z unit corresponds
            to 100 m of altitude. The current release operates in a 2.5D mode: routes are planned at a
            fixed mission altitude while the underlying terrain and threat fields are fully three-dimensional.
          </p>
          <ol>
            <li><strong>Terrain generation or CSV input.</strong> The environment is either procedurally
              generated from a deterministic seed or loaded from user-supplied CSV files describing
              elevation and terrain class per cell.</li>
            <li><strong>Threat placement and sensor definition.</strong> Radar, IR, acoustic, and visual
              sensors can be placed automatically using greedy, random, or strategic policies, defined
              by aggregate counts per type, entered as a full sensor table, or supplied via CSV.</li>
            <li><strong>Threat probability field.</strong> For each cell and each active sensor type, the
              pipeline evaluates a detection-probability field parameterised by the selected UAV's
              signature model (RCS, IR intensity, acoustic source level, visual area).</li>
            <li><strong>Cost-map generation.</strong> Terrain, no-fly zones, and per-sensor threat fields
              are combined into a scalar cost map used by the route planners.</li>
            <li><strong>Route planning.</strong> All supported planners — Dijkstra, A*, Ant Colony
              Optimization, a Genetic Algorithm, and a Monte Carlo / RL planner — are executed on the
              same cost map from the configured start to end point.</li>
            <li><strong>Algorithm comparison.</strong> Planners are compared on total path cost, wall-clock
              runtime, nodes visited, path length, and success status. Comparison plots and CSV metrics
              are produced when the backend reports them as available.</li>
          </ol>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">Design Notes</div>
        <div className="panel-body">
          <ul>
            <li>Frontend validation is provided for usability; the backend remains authoritative.</li>
            <li>Model-specific parameters (IR base intensity, acoustic idle level, aerodynamic coefficients)
              are labelled as <em>model units</em> until they are verified against physical measurements.</li>
            <li>Uploaded CSV content is treated as plain text and never rendered as HTML.</li>
            <li>Only algorithms exposed by the backend contribute measured metrics; missing outputs are
              shown as empty placeholders rather than fabricated values.</li>
          </ul>
        </div>
      </section>
    </div>
  );
}


