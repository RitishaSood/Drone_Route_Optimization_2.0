import numpy as np

class SuitabilityBuilder:

    @staticmethod
    def build_radar(
        elevation,
        visibility,
        strategic
    ):
        return (
            0.4*elevation +
            0.35*visibility +
            0.25*strategic
        )
    
    @staticmethod
    def build_visual(
        elevation,
        visibility,
        strategic
    ):
        return (
            0.2*elevation +
            0.5*visibility +
            0.3*strategic
        )

    @staticmethod
    def build_ir(
        elevation,
        visibility,
        strategic
    ):
        return (
            0.35*elevation +
            0.2*visibility +
            0.45*strategic
        )

    @staticmethod
    def build_acoustic(
        elevation,
        visibility,
        strategic
    ):
        return (
            0.35*(1-elevation) +
            0.15*visibility +
            0.5*strategic
        )