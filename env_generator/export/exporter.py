"""
exporter.py
===========

Exports placement outputs:

    sensor.csv
    nfz.csv

Terrain CSVs are exported separately by:

    terrain_exporter.py

Input:
    list[PlacedSensor]
    list[NFZ polygons]

Output:
    sensor.csv
    nfz.csv
"""

from __future__ import annotations
import csv
import os


class Exporter:

    def __init__(
        self,
        export_config
    ):

        self.cfg = export_config

        os.makedirs(
            self.cfg.data_dir,
            exist_ok=True
        )

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def export(
        self,
        sensors,
        nfz_polygons
    ):

        self.export_sensors(
            sensors
        )

        self.export_nfz(
            nfz_polygons
        )

    # --------------------------------------------------
    # sensor.csv
    # --------------------------------------------------

    def export_sensors(
        self,
        sensors
    ):

        with open(
            self.cfg.sensor_csv,
            "w",
            newline=""
        ) as file:

            writer = csv.writer(
                file
            )

            writer.writerow([
                "id",
                "sensor_type",
                "label",
                "x",
                "y",
                "z",
                "class"
            ])

            for sensor in sensors:

                writer.writerow(
                    sensor.to_csv_row()
                )

        print(
            f"[EXPORT] {self.cfg.sensor_csv}"
        )

    # --------------------------------------------------
    # nfz.csv
    # --------------------------------------------------

    def export_nfz(
        self,
        nfz_polygons
    ):

        with open(
            self.cfg.nfz_csv,
            "w",
            newline=""
        ) as file:

            writer = csv.writer(
                file
            )

            writer.writerow([
                "Cid",
                "type",
                "x1",
                "y1",
                "z1",
                "x2",
                "y2",
                "z2",
                "x3",
                "y3",
                "z3"
            ])

            for cid, polygon in enumerate(
                nfz_polygons,
                start=1
            ):

                p1 = polygon[0]
                p2 = polygon[1]
                p3 = polygon[2]

                writer.writerow([
                    cid,
                    "NFZ",
                    p1[0],
                    p1[1],
                    p1[2],
                    p2[0],
                    p2[1],
                    p2[2],
                    p3[0],
                    p3[1],
                    p3[2]
                ])

        print(
            f"[EXPORT] {self.cfg.nfz_csv}"
        )
    
    def export_env(
        self,
            env_config
        ):

            with open(
                self.cfg.env_csv,
                "w",
                newline=""
            ) as file:

                writer = csv.writer(
                    file
                )

                writer.writerow([
                    "parameter",
                    "value"
                ])

                writer.writerow([
                    "air_density",
                    env_config.air_density
                ])

                writer.writerow([
                    "wind_speed",
                    env_config.wind_speed
                ])

                writer.writerow([
                    "ir_gamma",
                    env_config.ir_gamma
                ])

                writer.writerow([
                    "ir_c_bg",
                    env_config.ir_c_bg
                ])

                writer.writerow([
                    "n_bg",
                    env_config.n_bg
                ])

                writer.writerow([
                    "visual_lux",
                    env_config.visual_lux
                ])

                writer.writerow([
                    "visual_c_bg",
                    env_config.visual_c_bg
                ])

            print(
                f"[EXPORT] {self.cfg.env_csv}"
            )