"""
visualization.py
================
All matplotlib visualisation for the UAV Sensor Placement System.

Style contract
--------------
All terrain base maps reuse the terrain team's exact conventions from
terraingeneration.py so that sensor overlays integrate naturally:
  - ListedColormap with tg.cmap_colors  ('#2B4C7E','#4A7C59',...)
  - BoundaryNorm with tg.bounds         ([0,150,350,600,800,1000])
  - Colorbar ticks at [75,250,475,700,900] labelled with tg.classes
  - origin='lower'  on every imshow call
  - Grid: alpha=0.3, linestyle='--'
  - xlabel='Grid X-Coordinate', ylabel='Grid Y-Coordinate'

Sensor symbols (per spec):
  radar    → '^'  red     #FF4444
  infrared → 's'  orange  #FF8800
  acoustic → 'o'  blue    #4488FF
  visual   → 'D'  green   #44FF44

Figures produced
----------------
  1. plot_terrain_with_sensors()  — terrain team base map + all sensors
  2. plot_suitability_grid()      — 2×2 grid of the four suitability maps
  3. plot_layer_grid()            — 2×2 grid of the three input layers + NFZ
  4. plot_elevation_3d()          — terrain team 3-D surface (no sensors)

Each method returns the Figure so main.py can save it.
show_plots=True in VizConfig triggers plt.show(block=False) per figure.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from config import SensorPlacementConfig, DEFAULT_CONFIG
from sensor_types import SENSOR_TYPES, PlacedSensor


class Visualizer:
    """
    Produces all figures for the sensor placement system.

    Parameters
    ----------
    tg  : TerrainGenerator  — live terrain object (owns cmap, bounds, classes)
    lb  : LayerBuilder      — provides layer arrays and suitability maps
    cfg : SensorPlacementConfig
    """

    def __init__(self, tg, lb, cfg: SensorPlacementConfig = DEFAULT_CONFIG):
        self.tg  = tg
        self.lb  = lb
        self.cfg = cfg
        self._dpi = cfg.viz.figure_dpi

        # ── Terrain team's exact colormap & norm (single source of truth) ──
        self._cmap = ListedColormap(tg.cmap_colors)
        self._norm = BoundaryNorm(tg.bounds, self._cmap.N)
        self._cbar_ticks  = [75, 250, 475, 700, 900]
        self._cbar_labels = tg.classes

        # Output directory
        os.makedirs(cfg.viz.output_dir, exist_ok=True)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _terrain_imshow(self, ax: plt.Axes) -> None:
        """
        Draw the terrain base layer on `ax` using the terrain team's exact
        colormap, norm, and origin.  Shared by every figure that shows terrain.
        """
        img = ax.imshow(
            self.tg.terrain,
            cmap=self._cmap,
            norm=self._norm,
            origin='lower',
        )
        cbar = plt.colorbar(img, ax=ax, ticks=self._cbar_ticks, shrink=0.85)
        cbar.ax.set_yticklabels(self._cbar_labels)
        cbar.set_label('Tactical Terrain Classification Level', fontsize=8)

    def _apply_grid_style(self, ax: plt.Axes, title: str) -> None:
        """Apply terrain team axis style to `ax`."""
        ax.set_title(title, fontsize=10, fontweight='bold', pad=6)
        ax.set_xlabel('Grid X-Coordinate', fontsize=8)
        ax.set_ylabel('Grid Y-Coordinate', fontsize=8)
        ax.grid(True, alpha=0.3, linestyle='--')

    def _overlay_nfz(self, ax: plt.Axes) -> None:
        """Draw NFZ exclusion circles as dashed red outlines."""
        for (nr, nc, radius) in self.lb.active_nfzs:
            circle = plt.Circle(
                (nc, nr), radius,
                color='red', fill=False,
                linestyle='--', linewidth=1.2, alpha=0.7,
            )
            ax.add_patch(circle)

    def _overlay_outposts(self, ax: plt.Axes) -> None:
        """Draw strategic high-ground outposts matching terrain team style."""
        if self.tg.high_ground_positions:
            hx, hy = zip(*self.tg.high_ground_positions)
            ax.scatter(
                hy, hx,
                color='white', marker='*', s=120,
                edgecolor='black', linewidth=0.7,
                zorder=5, label='Observation Outpost',
            )

    def _overlay_sensors(
        self,
        ax: plt.Axes,
        placed: List[PlacedSensor],
        sensor_type: Optional[str] = None,
    ) -> List[mpatches.Patch]:
        """
        Scatter-plot sensors onto `ax`.

        Parameters
        ----------
        sensor_type : if given, only plot sensors of that type.
                      If None, plot all types.

        Returns
        -------
        List of legend patch handles.
        """
        pc  = self.cfg.placement
        handles = []
        plotted_types = set()

        for st in SENSOR_TYPES:
            if sensor_type and st.name != sensor_type:
                continue

            sensors = [p for p in placed if p.sensor_type == st.name]
            if not sensors:
                continue

            rows = [s.row for s in sensors]
            cols = [s.col for s in sensors]
            color  = pc.colors[st.name]
            marker = pc.markers[st.name]

            ax.scatter(
                cols, rows,
                c=color, marker=marker,
                s=pc.marker_size, edgecolor='black',
                linewidth=0.8, zorder=6,
                label=f"{st.label} (n={len(sensors)})",
            )

            # Add sensor ID text labels
            for s in sensors:
                ax.annotate(
                    str(s.sensor_id),
                    (s.col, s.row),
                    textcoords='offset points', xytext=(4, 4),
                    fontsize=5, color='white',
                    fontweight='bold', zorder=7,
                )

            patch = mpatches.Patch(
                color=color,
                label=f"{st.label} (n={len(sensors)})"
            )
            handles.append(patch)
            plotted_types.add(st.name)

        return handles

    # -----------------------------------------------------------------------
    # Figure 1 — Terrain base + all sensors overlay
    # -----------------------------------------------------------------------

    def plot_terrain_with_sensors(
        self, placed: List[PlacedSensor]
    ) -> plt.Figure:
        """
        Primary output figure.

        Layout:
          - Terrain team base map (cmap + norm identical to tg.plot_2d)
          - NFZ exclusion circles (dashed red)
          - Strategic outposts (white stars)
          - All sensor types overlaid with their symbols and ID labels
          - Full legend in upper-right corner

        This is "Terrain Team Map + Sensor Network Overlay" as specified.
        """
        fig, ax = plt.subplots(figsize=(10, 8), dpi=self._dpi)

        # ── Terrain base (terrain team style) ──────────────────────────────
        self._terrain_imshow(ax)

        # ── NFZ exclusion zones ─────────────────────────────────────────────
        self._overlay_nfz(ax)
        nfz_patch = mpatches.Patch(
            edgecolor='red', facecolor='none',
            linestyle='--', linewidth=1.5,
            label=f'NFZ ({len(self.lb.active_nfzs)} active)',
        )

        # ── Strategic outposts ──────────────────────────────────────────────
        self._overlay_outposts(ax)
        outpost_patch = mpatches.Patch(
            color='white', label=f'Outpost ({len(self.tg.high_ground_positions)})',
        )

        # ── Sensor overlays ─────────────────────────────────────────────────
        sensor_handles = self._overlay_sensors(ax, placed)

        # ── Legend ──────────────────────────────────────────────────────────
        all_handles = sensor_handles + [nfz_patch, outpost_patch]
        ax.legend(
            handles=all_handles,
            loc='upper left', fontsize=7,
            framealpha=0.85, edgecolor='white',
        )

        # ── Sensor count annotation ─────────────────────────────────────────
        count_lines = [f"Total sensors: {len(placed)}"]
        for st in SENSOR_TYPES:
            n = sum(1 for p in placed if p.sensor_type == st.name)
            count_lines.append(f"  {st.label}: {n}")
        ax.text(
            0.99, 0.01, '\n'.join(count_lines),
            transform=ax.transAxes,
            fontsize=6.5, verticalalignment='bottom',
            horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='black',
                      alpha=0.65, edgecolor='white'),
            color='white',
        )

        self._apply_grid_style(
            ax, "UAV Sensor Network — Terrain + Placement Overlay"
        )

        fig.tight_layout()
        if self.cfg.viz.show_plots:
            plt.show(block=False)
        return fig

    # -----------------------------------------------------------------------
    # Figure 2 — 2×2 suitability map grid
    # -----------------------------------------------------------------------

    def plot_suitability_grid(self, placed: List[PlacedSensor]) -> plt.Figure:
        """
        2×2 subplot grid showing the suitability map for each sensor type
        with its placed sensors overlaid.

        Each subplot:
          - plasma colormap for the suitability score [0, 1]
          - NFZ mask shown as dark overlay (alpha hatching)
          - Placed sensors of that type only
          - Colorbar labelled 'Suitability Score'
        """
        fig, axes = plt.subplots(2, 2, figsize=(13, 10), dpi=self._dpi)
        axes_flat = axes.flatten()

        nfz_display = np.ma.masked_where(
            self.lb.nfz_mask == 0,
            np.ones_like(self.lb.nfz_mask, dtype=float),
        )

        for idx, st in enumerate(SENSOR_TYPES):
            ax   = axes_flat[idx]
            suit = self.lb.suitability_maps[st.name]

            # Suitability heatmap
            img = ax.imshow(
                suit, cmap='plasma', vmin=0, vmax=1, origin='lower',
            )
            cbar = plt.colorbar(img, ax=ax, shrink=0.85)
            cbar.set_label('Suitability Score', fontsize=7)
            cbar.ax.tick_params(labelsize=6)

            # NFZ overlay (dark semi-transparent)
            ax.imshow(
                nfz_display, cmap='Reds', alpha=0.4,
                vmin=0, vmax=1, origin='lower',
            )

            # Sensors of this type
            self._overlay_sensors(ax, placed, sensor_type=st.name)

            # Strategic outposts
            self._overlay_outposts(ax)

            n = sum(1 for p in placed if p.sensor_type == st.name)
            self._apply_grid_style(
                ax,
                f"{st.label} Suitability  "
                f"(w_e={self.cfg.weights.__dict__[st.weight_key]['elevation']:.2f}  "
                f"w_v={self.cfg.weights.__dict__[st.weight_key]['visibility']:.2f}  "
                f"w_s={self.cfg.weights.__dict__[st.weight_key]['strategic']:.2f})  "
                f"— {n} placed"
            )

            ax.legend(fontsize=6, loc='upper right', framealpha=0.8)

        fig.suptitle(
            "Suitability Maps per Sensor Type  (red overlay = NFZ)",
            fontsize=12, fontweight='bold', y=1.01,
        )
        fig.tight_layout()
        if self.cfg.viz.show_plots:
            plt.show(block=False)
        return fig

    # -----------------------------------------------------------------------
    # Figure 3 — 2×2 input layer grid
    # -----------------------------------------------------------------------

    def plot_layer_grid(self) -> plt.Figure:
        """
        2×2 subplot grid of the four input layers:
          [0,0] Elevation layer   (viridis)
          [0,1] Strategic layer   (YlOrRd)
          [1,0] Visibility layer  (RdYlGn)
          [1,1] NFZ mask          (terrain base + NFZ circles)
        """
        fig, axes = plt.subplots(2, 2, figsize=(13, 10), dpi=self._dpi)

        layers = [
            (self.lb.elevation_layer,  'viridis', 'Elevation Layer  (normalised)'),
            (self.lb.strategic_layer,  'YlOrRd',  'Strategic Importance Layer'),
            (self.lb.visibility_layer, 'RdYlGn',  'Visibility Layer  (heuristic)'),
        ]

        for idx, (arr, cmap_name, title) in enumerate(layers):
            ax  = axes.flatten()[idx]
            img = ax.imshow(arr, cmap=cmap_name, vmin=0, vmax=1, origin='lower')
            cbar = plt.colorbar(img, ax=ax, shrink=0.85)
            cbar.set_label('Normalised Score [0–1]', fontsize=7)
            cbar.ax.tick_params(labelsize=6)
            self._apply_grid_style(ax, title)

            # Mark strategic outposts on strategic layer subplot
            if idx == 1:
                self._overlay_outposts(ax)
                if self.tg.high_ground_positions:
                    ax.legend(fontsize=6, loc='upper right')

        # Bottom-right: terrain base + NFZ exclusion zones
        ax_nfz = axes[1][1]
        self._terrain_imshow(ax_nfz)
        self._overlay_nfz(ax_nfz)
        nfz_patch = mpatches.Patch(
            edgecolor='red', facecolor='none', linestyle='--',
            label=f'NFZ  ({len(self.lb.active_nfzs)} active)',
        )
        ax_nfz.legend(handles=[nfz_patch], fontsize=7, loc='upper right')
        self._apply_grid_style(
            ax_nfz,
            f"Active NFZ Mask  ({len(self.lb.active_nfzs)} zones, "
            f"{int(self.lb.nfz_mask.sum())} cells restricted)"
        )

        fig.suptitle(
            "Input Layers — Phase 2 Layer Builder",
            fontsize=12, fontweight='bold', y=1.01,
        )
        fig.tight_layout()
        if self.cfg.viz.show_plots:
            plt.show(block=False)
        return fig

    # -----------------------------------------------------------------------
    # Figure 4 — 3-D terrain surface (terrain team style, no sensors)
    # -----------------------------------------------------------------------

    def plot_elevation_3d(self) -> plt.Figure:
        """
        3-D surface plot following the terrain team's plot_3d() conventions:
          - cmap='terrain', edgecolor='none', alpha=0.9
          - view_init(elev=38, azim=-125)
          - zlim(0, 1000)
        High-ground outposts plotted as red scatter on the surface.
        """
        from mpl_toolkits.mplot3d import Axes3D   # noqa: F401

        fig = plt.figure("3D Sensor Terrain", figsize=(11, 8), dpi=self._dpi)
        ax  = fig.add_subplot(111, projection='3d')

        n   = self.tg.grid_size
        x   = np.arange(0, n)
        y   = np.arange(0, n)
        xx, yy = np.meshgrid(x, y)

        # Surface — terrain team style
        surf = ax.plot_surface(
            xx, yy, self.tg.terrain,
            cmap='terrain', edgecolor='none', alpha=0.9, linewidth=0,
        )
        fig.colorbar(
            surf, ax=ax, shrink=0.5, aspect=10,
            label='Elevation (Metres)',
        )

        # Strategic outposts on surface
        for (pr, pc) in self.tg.high_ground_positions:
            ax.scatter(
                pc, pr, self.tg.terrain[pr, pc] + 15,
                color='red', marker='^', s=80, zorder=5,
            )

        ax.set_title(
            "3D Battlefield Terrain — Sensor Placement Reference",
            fontweight='bold',
        )
        ax.set_xlabel("Grid X")
        ax.set_ylabel("Grid Y")
        ax.set_zlabel("Elevation (m)")
        ax.set_zlim(0, 1000)
        ax.view_init(elev=38, azim=-125)

        fig.tight_layout()
        if self.cfg.viz.show_plots:
            plt.show(block=False)
        return fig

    # -----------------------------------------------------------------------
    # Save helper
    # -----------------------------------------------------------------------

    def save(self, fig: plt.Figure, filename: str) -> str:
        """
        Save `fig` to cfg.viz.output_dir/<filename>.
        Returns the full output path.
        """
        path = os.path.join(self.cfg.viz.output_dir, filename)
        fig.savefig(path, dpi=self._dpi, bbox_inches='tight')
        return path


# ---------------------------------------------------------------------------
# Self-test  (headless — saves PNGs, does not open windows)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import numpy as _np
    import random as _random

    sys.path.insert(0, ".")
    matplotlib_backend = plt.get_backend()

    # Use non-interactive backend for self-test
    plt.switch_backend('Agg')

    from terraingeneration import TerrainGenerator
    from config import DEFAULT_CONFIG, SensorPlacementConfig
    from layer_builder import LayerBuilder
    from placement_engine import PlacementEngine

    seed = 42
    _np.random.seed(seed)

    tg = TerrainGenerator(
        grid_size=100, scale=40.0, octaves=6,
        persistence=0.5, lacunarity=2.0, seed=seed,
    )
    tg.generate_base_terrain()
    tg.add_ridges(num_ridges=4, ridge_height=180, ridge_width=6.0)
    tg.add_valleys(num_valleys=2, valley_depth=150, valley_width=10.0)
    tg.classify_terrain()
    tg.calculate_slope()
    tg.generate_cost_map()

    cfg = SensorPlacementConfig()
    cfg.viz.show_plots = False   # headless

    lb = LayerBuilder(tg, cfg)
    engine = PlacementEngine(tg, lb, cfg)
    placed = engine.place({'radar': 6, 'visual': 8, 'infrared': 6, 'acoustic': 8})

    viz = Visualizer(tg, lb, cfg)

    print("Rendering Figure 1: terrain + sensor overlay...")
    fig1 = viz.plot_terrain_with_sensors(placed)
    p1 = viz.save(fig1, "fig1_terrain_sensors.png")
    print(f"  Saved → {p1}")

    print("Rendering Figure 2: suitability grid...")
    fig2 = viz.plot_suitability_grid(placed)
    p2 = viz.save(fig2, "fig2_suitability_grid.png")
    print(f"  Saved → {p2}")

    print("Rendering Figure 3: layer grid...")
    fig3 = viz.plot_layer_grid()
    p3 = viz.save(fig3, "fig3_layer_grid.png")
    print(f"  Saved → {p3}")

    print("Rendering Figure 4: 3D elevation...")
    fig4 = viz.plot_elevation_3d()
    p4 = viz.save(fig4, "fig4_elevation_3d.png")
    print(f"  Saved → {p4}")

    # Verify files exist and are non-empty
    import os
    for path in [p1, p2, p3, p4]:
        size = os.path.getsize(path)
        assert size > 10_000, f"{path} suspiciously small ({size} bytes)"
        print(f"PASS  {os.path.basename(path)}  ({size//1024} KB)")

    plt.close('all')
    print("\nAll visualization.py checks passed.")