"""
main.py
=======
Entry point for the UAV Sensor Placement Simulation.

Orchestration order
-------------------
1.  Resolve matplotlib backend BEFORE any pyplot import
2.  Parse CLI arguments
3.  Initialise seed (random or fixed)
4.  Generate terrain via terraingeneration.py
5.  Validate config and sensor registry
6.  Build input layers (LayerBuilder)
7.  Prompt user for sensor counts
8.  Run greedy placement (PlacementEngine)
9.  Render and save all figures (Visualizer)
10. Export sensor_map.json (Exporter)
11. Print final summary

Usage
-----
    python main.py                    # random seed, interactive counts
    python main.py --seed 42          # fixed seed for reproducibility
    python main.py --seed 42 --auto   # fixed seed, default counts
    python main.py --no-plots         # headless: save PNGs, no display
    python main.py --seed 42 --auto --no-plots   # fully non-interactive
"""

from __future__ import annotations

# ── Step 1: resolve backend BEFORE any pyplot import ─────────────────────────
# visualization.py imports matplotlib.pyplot at module level.  We must set the
# backend here, before that module is imported, to avoid the
# "Cannot load backend after matplotlib has been imported" warning / failure.
import sys
import argparse

def _parse_no_plots_early() -> bool:
    """Lightweight pre-scan of sys.argv for --no-plots before full argparse."""
    return "--no-plots" in sys.argv

_HEADLESS = _parse_no_plots_early()

import matplotlib
matplotlib.use("Agg" if _HEADLESS else matplotlib.get_backend())
# pyplot itself must NOT be imported here; let visualization.py own that.

# ── Standard library ─────────────────────────────────────────────────────────
import os
import random
import time
import traceback
from typing import Dict, List, Optional

# ── Third-party ───────────────────────────────────────────────────────────────
import numpy as np

# ── Project imports ───────────────────────────────────────────────────────────
# All project modules imported at the top so missing files surface immediately.
from terraingeneration import TerrainGenerator
from config import SensorPlacementConfig
from sensor_types import SENSOR_TYPES, PlacedSensor, validate_registry
from layer_builder import LayerBuilder
from placement_engine import PlacementEngine
from visualization import Visualizer
from exporter import Exporter


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default counts used in --auto mode and as prompt fallbacks.
# Must contain a key for every name in SENSOR_TYPES.
_DEFAULT_COUNTS: Dict[str, int] = {
    'radar':    6,
    'visual':   8,
    'infrared': 6,
    'acoustic': 8,
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="UAV Terrain-Aware Sensor Placement System — Phase 2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py\n"
            "  python main.py --seed 42\n"
            "  python main.py --seed 42 --auto\n"
            "  python main.py --no-plots --auto\n"
        ),
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Terrain generation seed (default: random integer)",
    )
    parser.add_argument(
        "--no-plots", action="store_true",
        help="Save figures to disk only — do not open display windows",
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Use default sensor counts without interactive prompts",
    )
    return parser


# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------

def _banner(text: str) -> None:
    w = 64
    print("\n" + "=" * w)
    print(f"  {text}")
    print("=" * w)


def _step(label: str) -> None:
    """Print a numbered step header. Counter is automatic."""
    _step.n += 1
    print(f"\n[{_step.n}] {label}")

_step.n = 0  # type: ignore[attr-defined]


def _ok(msg: str) -> None:
    print(f"    ✓  {msg}")


def _warn(msg: str) -> None:
    print(f"    ⚠  {msg}", file=sys.stderr)


def _err(msg: str) -> None:
    print(f"    ✗  {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Sensor count prompt
# ---------------------------------------------------------------------------

def _prompt_sensor_counts() -> Dict[str, int]:
    """
    Interactively prompt for sensor counts per type.
    Blank input accepts the default shown in brackets.
    Validates non-negative integers; re-prompts on bad input.
    Handles EOF (Ctrl-D in terminal / Colab interruption) gracefully.
    """
    print("\n  Enter sensor counts  (press Enter to accept default shown):")
    counts: Dict[str, int] = {}

    for st in SENSOR_TYPES:
        default = _DEFAULT_COUNTS.get(st.name, 0)
        while True:
            try:
                raw = input(f"    {st.label:<16} [{default}]: ").strip()
            except EOFError:
                # Non-interactive environment — fall back to default silently
                counts[st.name] = default
                print(f"    {st.label:<16} → {default}  (default, EOF)")
                break

            if raw == "":
                counts[st.name] = default
                break

            try:
                val = int(raw)
                if val < 0:
                    raise ValueError("negative")
                counts[st.name] = val
                break
            except ValueError:
                print("      ✗  Please enter a non-negative integer.")

    return counts


# ---------------------------------------------------------------------------
# Figure rendering helper
# ---------------------------------------------------------------------------

def _render_and_save(
    viz: Visualizer,
    method_name: str,
    filename: str,
    method_kwargs: Optional[dict] = None,
) -> bool:
    """
    Call a Visualizer method, save the result, and close the figure.
    Isolates failures so one bad plot does not abort the whole run.

    Returns True on success, False on failure.
    """
    import matplotlib.pyplot as plt  # safe — backend already set at module top

    try:
        method = getattr(viz, method_name)
        fig = method(**(method_kwargs or {}))
        path = viz.save(fig, filename)
        _ok(f"Saved → {path}")
        plt.close(fig)
        return True
    except Exception:
        _err(f"Figure '{filename}' failed — continuing without it.")
        traceback.print_exc()
        plt.close("all")
        return False


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()
    t_start = time.perf_counter()

    _banner("UAV Terrain-Aware Sensor Placement System  —  Phase 2")

    # ── 1. Seed ──────────────────────────────────────────────────────────────
    _step("Initialising runtime seed")
    seed = 42
    np.random.seed(seed)
    random.seed(seed)
    print(f"    Seed  : {seed}")
    print(f"    Mode  : {'headless (--no-plots)' if args.no_plots else 'interactive'}")
    print(f"    Counts: {'auto (--auto)' if args.auto else 'user prompt'}")

    # ── 2. Config ─────────────────────────────────────────────────────────────
    _step("Loading and validating configuration")
    try:
        cfg = SensorPlacementConfig()
        cfg.viz.show_plots = not args.no_plots

        # Propagate seed to NFZ random selection so full run is reproducible
        # when --seed is supplied.  None → random NFZ layout each run.
        if args.seed is not None:
            cfg.nfz.nfz_random_seed = seed

        cfg.validate()
        validate_registry(cfg)
        _ok("config.validate() passed")
        _ok("validate_registry() passed")
    except Exception as exc:
        _err(f"Configuration error: {exc}")
        sys.exit(1)

    # Ensure output directory exists early so later steps don't fail silently
    os.makedirs(cfg.viz.output_dir, exist_ok=True)

    # ── 3. Terrain generation ─────────────────────────────────────────────────
    _step("Generating terrain  (terraingeneration.py)")
    
    try:
        print("DEBUG 1")
        tg = TerrainGenerator(
            grid_size=100,
            scale=40.0,
            octaves=6,
            persistence=0.5,
            lacunarity=2.0,
            seed=seed,
        )
        print("DEBUG A")
        tg.generate_base_terrain()

        print("DEBUG B")
        tg.add_ridges(
    num_ridges=20,
    ridge_height=180,
    ridge_width=6.0
)

        print("DEBUG C")
        tg.add_valleys(
    num_valleys=2,
    valley_depth=150,
    valley_width=10.0
)

        print("DEBUG D")
        tg.classify_terrain()

        print("DEBUG E")
        tg.calculate_slope()

        print("DEBUG F")
        tg.generate_cost_map()

        print("DEBUG G")
    except Exception as exc:
        _err(f"Terrain generation failed: {exc}")
        traceback.print_exc()
        sys.exit(1)

    km = tg.grid_size * cfg.terrain.cell_size_m / 1000
    print(f"    Grid              : {tg.grid_size} × {tg.grid_size} cells  ({km:.0f} km × {km:.0f} km)")
    print(f"    Elevation range   : {tg.terrain.min():.1f} – {tg.terrain.max():.1f} m")
    print(f"    Terrain classes   : {tg.classes}")
    print(f"    Strategic outposts: {len(tg.high_ground_positions)}")
    for pos in tg.high_ground_positions:
        print(f"      ({pos[0]:3d},{pos[1]:3d})  "
              f"elev={tg.terrain[pos[0], pos[1]]:.0f} m  "
              f"class={tg.terrain_type[pos[0], pos[1]]}")

    # ── 4. Layer builder ──────────────────────────────────────────────────────
    _step("Building input layers  (LayerBuilder)")
    try:
        lb = LayerBuilder(tg, cfg)
    except Exception as exc:
        _err(f"LayerBuilder failed: {exc}")
        traceback.print_exc()
        sys.exit(1)

    print(f"    Elevation layer  : mean={lb.elevation_layer.mean():.3f}")
    print(f"    Strategic layer  : mean={lb.strategic_layer.mean():.3f}  "
          f"({len(tg.high_ground_positions)} outpost(s))")
    print(f"    Visibility layer : mean={lb.visibility_layer.mean():.3f}")
    print(f"    NFZ mask         : {int(lb.nfz_mask.sum())} cells restricted  "
          f"({len(lb.active_nfzs)} active zones)")
    for nfz in lb.active_nfzs:
        print(f"      NFZ @ ({nfz[0]:3d},{nfz[1]:3d})  r={nfz[2]} cells")
    print(f"    Suitability maps : {list(lb.suitability_maps.keys())}")

    # ── 5. Sensor counts ──────────────────────────────────────────────────────
    _step("Sensor counts")
    if args.auto:
        counts = {st.name: _DEFAULT_COUNTS.get(st.name, 0) for st in SENSOR_TYPES}
        print("    Using default counts (--auto):")
    else:
        counts = _prompt_sensor_counts()
        print("\n    Confirmed counts:")

    for st in SENSOR_TYPES:
        print(f"      {st.label:<16}: {counts[st.name]}")
    total_requested = sum(counts.values())
    print(f"      {'Total':<16}: {total_requested}")

    if total_requested == 0:
        _warn("All sensor counts are zero — nothing to place. Exiting.")
        sys.exit(0)

    # ── 6. Placement ──────────────────────────────────────────────────────────
    _step(f"Greedy placement  ({total_requested} sensors requested)")
    try:
        engine = PlacementEngine(tg, lb, cfg)
        placed = engine.place(counts)
    except Exception as exc:
        _err(f"PlacementEngine failed: {exc}")
        traceback.print_exc()
        sys.exit(1)

    total_placed = len(placed)
    if total_placed < total_requested:
        _warn(f"Only {total_placed} / {total_requested} sensors placed "
              f"(separation / NFZ constraints).")
    else:
        _ok(f"All {total_placed} sensors placed successfully.")

    print(engine.summary(placed))

    # ── 7. Visualisation ──────────────────────────────────────────────────────
    _step("Rendering figures  (Visualizer)")
    viz = Visualizer(tg, lb, cfg)
    figures_ok: List[bool] = []

    figures_ok.append(_render_and_save(
        viz, "plot_terrain_with_sensors", "fig1_terrain_sensors.png",
        {"placed": placed},
    ))
    figures_ok.append(_render_and_save(
        viz, "plot_suitability_grid", "fig2_suitability_grid.png",
        {"placed": placed},
    ))
    figures_ok.append(_render_and_save(
        viz, "plot_layer_grid", "fig3_layer_grid.png",
    ))
    figures_ok.append(_render_and_save(
        viz, "plot_elevation_3d", "fig4_elevation_3d.png",
    ))

    n_figs_ok = sum(figures_ok)
    if n_figs_ok == len(figures_ok):
        _ok(f"All {n_figs_ok} figures saved to {cfg.viz.output_dir}/")
    else:
        _warn(f"{n_figs_ok}/{len(figures_ok)} figures saved — see errors above.")

    # Show interactive windows only if requested and at least one figure was built
    if not args.no_plots and n_figs_ok > 0:
        import matplotlib.pyplot as plt
        print("\n    Figures open in display windows.")
        print("    Close all windows or press Ctrl-C to continue.")
        try:
            plt.show()
        except KeyboardInterrupt:
            pass
        finally:
            plt.close("all")

    # ── 8. Export ─────────────────────────────────────────────────────────────
    _step("Exporting sensor_map.json  (Exporter)")
    try:
        exporter  = Exporter(tg, lb, cfg)
        json_path = exporter.export(placed, seed=seed)
        _ok(f"Exported → {json_path}")
    except Exception as exc:
        _err(f"Export failed: {exc}")
        traceback.print_exc()
        # Export failure is non-fatal — placement results are already printed

    # ── 9. Final summary ──────────────────────────────────────────────────────
    elapsed = time.perf_counter() - t_start
    _banner("Run Complete")
    print(f"  Seed              : {seed}")
    print(f"  Sensors placed    : {total_placed} / {total_requested} requested")
    for st in SENSOR_TYPES:
        n = sum(1 for p in placed if p.sensor_type == st.name)
        print(f"    {st.label:<16}: {n}")
    print(f"  Figures saved     : {n_figs_ok}/{len(figures_ok)}")
    print(f"  Output directory  : {cfg.viz.output_dir}/")
    print(f"  Elapsed           : {elapsed:.2f}s")
    print("=" * 64)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()