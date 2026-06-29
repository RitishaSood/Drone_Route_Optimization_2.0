import random


class NFZGenerator:

    NFZ_LIBRARY = [

        [(8,8,0), (28,22,0), (15,35,0)],
        [(35,12,0), (58,25,0), (40,42,0)],
        [(70,10,0), (92,28,0), (78,45,0)],
        [(12,55,0), (30,78,0), (8,88,0)],
        [(42,48,0), (68,55,0), (55,82,0)],

        [(72,60,0), (95,72,0), (82,92,0)],
        [(18,35,0), (38,52,0), (10,62,0)],
        [(55,2,0), (78,15,0), (58,30,0)],
        [(2,72,0), (18,92,0), (0,98,0)],
        [(68,38,0), (92,58,0), (72,72,0)]
    ]

    @staticmethod
    def generate(
        seed,
        count=4
    ):

        rng = random.Random(seed)

        selected = rng.sample(
            NFZGenerator.NFZ_LIBRARY,
            count
        )

        for poly in selected:

            for x, y, z in poly:

                assert 0 <= x < 100
                assert 0 <= y < 100
                assert 0 <= z < 100

        return selected