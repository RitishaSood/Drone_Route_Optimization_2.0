import numpy as np

class CSVLoader:

    @staticmethod
    def load_height(path):
        return np.loadtxt(path, delimiter=",")

    @staticmethod
    def load_terrain(path):
        return np.loadtxt(
            path,
            delimiter=",",
            dtype=np.uint8
        )