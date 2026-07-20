import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { DRONES, type DroneRecord } from "@/data/drones";

export const Route = createFileRoute("/drones")({
  component: DronesPage,
});

type NumKey =
  | "max_speed"
  | "ceiling"
  | "mtow"
  | "wingspan"
  | "length"
  | "wing_area"
  | "stall_speed"
  | "max_wind_tolerance"
  | "failure_probability";
type SortKey = "name" | NumKey;

const COLUMNS: { key: keyof DroneRecord; label: string; numeric?: boolean; sortable?: boolean }[] =
  [
    { key: "name", label: "Drone Name", sortable: true },
    { key: "uav_class", label: "UAV Class" },
    { key: "propulsion_class", label: "Propulsion" },
    { key: "max_speed", label: "Max Speed (m/s)", numeric: true, sortable: true },
    { key: "ceiling", label: "Service Ceiling (m)", numeric: true, sortable: true },
    { key: "mtow", label: "MTOW (kg)", numeric: true, sortable: true },
    { key: "wingspan", label: "Wingspan (m)", numeric: true, sortable: true },
    { key: "length", label: "Length (m)", numeric: true, sortable: true },
    { key: "wing_area", label: "Wing Area (m²)", numeric: true, sortable: true },
    { key: "stall_speed", label: "Stall Speed (m/s)", numeric: true, sortable: true },
    { key: "max_wind_tolerance", label: "Max Wind Tolerance (m/s)", numeric: true, sortable: true },
    { key: "sigma_front", label: "Front RCS σ (m²)", numeric: true },
    { key: "sigma_side", label: "Side RCS σ (m²)", numeric: true },
    { key: "sigma_avg", label: "Average RCS σ (m²)", numeric: true },
    { key: "i_base", label: "IR Base Intensity (model units)", numeric: true },
    { key: "c_drag", label: "IR Drag Coefficient (model units)", numeric: true },
    { key: "s_idle", label: "Acoustic Idle Source Level (model units)", numeric: true },
    { key: "c_aero", label: "Acoustic Aero Coefficient (model units)", numeric: true },
    { key: "a_vis", label: "Visual Area (m²)", numeric: true },
    { key: "failure_probability", label: "Failure Probability", numeric: true, sortable: true },
  ];

function DronesPage() {
  const [q, setQ] = useState("");
  const [uavClass, setUavClass] = useState("");
  const [prop, setProp] = useState("");
  const [sort, setSort] = useState<SortKey>("name");
  const [dir, setDir] = useState<"asc" | "desc">("asc");
  const [visible, setVisible] = useState<Set<string>>(new Set(COLUMNS.map((c) => c.key)));
  const [showColPanel, setShowColPanel] = useState(false);
  const [selected, setSelected] = useState<DroneRecord | null>(null);

  const uavClasses = useMemo(() => Array.from(new Set(DRONES.map((d) => d.uav_class))).sort(), []);
  const props = useMemo(
    () => Array.from(new Set(DRONES.map((d) => d.propulsion_class))).sort(),
    [],
  );

  const rows = useMemo(() => {
    let r = DRONES.filter((d) => {
      if (uavClass && d.uav_class !== uavClass) return false;
      if (prop && d.propulsion_class !== prop) return false;
      if (q) {
        const s = q.toLowerCase();
        if (!(
          d.name.toLowerCase().includes(s) ||
          d.uav_class.toLowerCase().includes(s) ||
          d.propulsion_class.toLowerCase().includes(s)
        ))
          return false;
      }
      return true;
    });
    r = [...r].sort((a, b) => {
      const av = a[sort];
      const bv = b[sort];
      if (typeof av === "number" && typeof bv === "number")
        return dir === "asc" ? av - bv : bv - av;
      return dir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return r;
  }, [q, uavClass, prop, sort, dir]);

  const toggleCol = (k: string) => {
    const s = new Set(visible);
    if (s.has(k)) s.delete(k);
    else s.add(k);
    setVisible(s);
  };
  const sortBy = (k: SortKey) => {
    if (sort === k) setDir(dir === "asc" ? "desc" : "asc");
    else {
      setSort(k);
      setDir("asc");
    }
  };

  return (
    <div className="page">
      <header className="app-header">
        <h1>Drone Database</h1>
        <div className="subtitle">
          Static UAV parameters used by the cost-field and threat-probability models.
        </div>
      </header>

      <div className="alert alert-info">
        Static UAV parameters are used by the cost-field and threat-probability models. Dynamic
        fields such as current speed and heading are not shown here.
      </div>

      <section className="panel">
        <div className="panel-header">
          <span>Platforms ({rows.length})</span>
          <span className="row" style={{ gap: 6 }}>
            <button className="btn btn-sm" onClick={() => setShowColPanel((v) => !v)}>
              Columns
            </button>
          </span>
        </div>
        <div className="panel-body">
          <div className="form-grid">
            <div>
              <label htmlFor="q">Search</label>
              <input
                id="q"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Name, class, propulsion"
              />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <div>
                <label htmlFor="uc">UAV class</label>
                <select id="uc" value={uavClass} onChange={(e) => setUavClass(e.target.value)}>
                  <option value="">All</option>
                  {uavClasses.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="pp">Propulsion</label>
                <select id="pp" value={prop} onChange={(e) => setProp(e.target.value)}>
                  <option value="">All</option>
                  {props.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          {showColPanel && (
            <div className="panel" style={{ margin: "12px 0 0" }}>
              <div className="panel-header">Column visibility</div>
              <div className="panel-body checkbox-group" style={{ border: "none" }}>
                {COLUMNS.map((c) => (
                  <label key={c.key}>
                    <input
                      type="checkbox"
                      checked={visible.has(c.key)}
                      onChange={() => toggleCol(c.key)}
                    />
                    {c.label}
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="table-wrap compact">
          <table className="table">
            <thead>
              <tr>
                {COLUMNS.filter((c) => visible.has(c.key)).map((c) => (
                  <th key={c.key} className={c.numeric ? "num" : ""}>
                    {c.sortable ? (
                      <button className="sort-btn" onClick={() => sortBy(c.key as SortKey)}>
                        {c.label} {sort === c.key ? (dir === "asc" ? "▲" : "▼") : ""}
                      </button>
                    ) : (
                      c.label
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((d) => (
                <tr
                  key={d.name}
                  onClick={() => setSelected(d)}
                  style={{ cursor: "pointer" }}
                  className={selected?.name === d.name ? "selected" : ""}
                >
                  {COLUMNS.filter((c) => visible.has(c.key)).map((c) => (
                    <td key={c.key} className={c.numeric ? "num" : ""}>
                      {String(d[c.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {selected && <DroneDetail drone={selected} onClose={() => setSelected(null)} />}

      <div className="alert alert-warn" style={{ marginTop: 12 }}>
        Units are based on the current DroneState model. Fields marked as “model units” should be
        verified before being used as physical measurements in reports.
      </div>
    </div>
  );
}

function DroneDetail({ drone, onClose }: { drone: DroneRecord; onClose: () => void }) {
  const g = (label: string, v: string) => (
    <>
      <dt>{label}</dt>
      <dd>{v}</dd>
    </>
  );
  return (
    <section className="drone-detail" style={{ marginTop: 20 }}>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
        <h3>{drone.name}</h3>
        <button className="btn btn-sm" onClick={onClose}>
          Close
        </button>
      </div>

      <div className="group-title">Identity</div>
      <dl className="dl-grid">
        {g("UAV class", drone.uav_class)}
        {g("Propulsion", drone.propulsion_class)}
      </dl>

      <div className="group-title">Performance</div>
      <dl className="dl-grid">
        {g("Max speed", `${drone.max_speed} m/s`)}
        {g("Stall speed", `${drone.stall_speed} m/s`)}
        {g("Ceiling", `${drone.ceiling} m`)}
        {g("Max wind tolerance", `${drone.max_wind_tolerance} m/s`)}
      </dl>

      <div className="group-title">Geometry</div>
      <dl className="dl-grid">
        {g("MTOW", `${drone.mtow} kg`)}
        {g("Wingspan", `${drone.wingspan} m`)}
        {g("Length", `${drone.length} m`)}
        {g("Wing area", `${drone.wing_area} m²`)}
      </dl>

      <div className="group-title">Radar / Signature</div>
      <dl className="dl-grid">
        {g("Front RCS σ", `${drone.sigma_front} m²`)}
        {g("Side RCS σ", `${drone.sigma_side} m²`)}
        {g("Average RCS σ", `${drone.sigma_avg} m²`)}
      </dl>

      <div className="group-title">IR Model</div>
      <dl className="dl-grid">
        {g("Base intensity", `${drone.i_base} (model units)`)}
        {g("Drag coefficient", `${drone.c_drag} (model units)`)}
      </dl>

      <div className="group-title">Acoustic Model</div>
      <dl className="dl-grid">
        {g("Idle source level", `${drone.s_idle} (model units)`)}
        {g("Aero coefficient", `${drone.c_aero} (model units)`)}
      </dl>

      <div className="group-title">Visual Model</div>
      <dl className="dl-grid">{g("Visual area", `${drone.a_vis} m²`)}</dl>

      <div className="group-title">Reliability</div>
      <dl className="dl-grid">{g("Failure probability", String(drone.failure_probability))}</dl>
    </section>
  );
}
