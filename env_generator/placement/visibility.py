import numpy as np

from terrain.terrain_constants import *

class VisibilityLayerGenerator:

    SCORES = {

        WATER: 0.1,

        PLAIN: 0.4,

        FOREST: 0.3,

        HILL: 0.7,

        VALLEY: 0.2,

        MOUNTAIN: 1.0
    }

    @classmethod
    def build(
        cls,
        terrain_map
    ):

        layer = np.zeros_like(
            terrain_map,
            dtype=np.float32
        )

        for terrain_id, score in cls.SCORES.items():

            layer[
                terrain_map == terrain_id
            ] = score

        return layer