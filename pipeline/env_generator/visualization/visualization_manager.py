from visualization.terrain_plot import TerrainPlot
from visualization.sensor_plot import SensorPlot
from visualization.suitability_plot import SuitabilityPlot
from visualization.layer_plot import LayerPlot
from visualization.terrain_3d_plot import Terrain3DPlot
from visualization.save_utils import SaveUtils


class VisualizationManager:

    def __init__(
        self,
        output_dir
    ):

        self.output_dir = output_dir

    def terrain(
        self,
        terrain_map
    ):

        return TerrainPlot.create(
            terrain_map
        )

    def sensors(
        self,
        terrain_map,
        sensors
    ):

        return SensorPlot.create(
            terrain_map,
            sensors
        )

    def suitability(
        self,
        suitability_maps
    ):

        return SuitabilityPlot.create(
            suitability_maps
        )

    def layers(
        self,
        elevation_layer,
        visibility_layer,
        strategic_layer,
        nfz_mask
    ):

        return LayerPlot.create(
            elevation_layer,
            visibility_layer,
            strategic_layer,
            nfz_mask
        )

    def terrain_3d(
        self,
        height_map
    ):

        return Terrain3DPlot.create(
            height_map
        )

    def save(
        self,
        fig,
        filename
    ):

        return SaveUtils.save_figure(
            fig,
            self.output_dir,
            filename
        )