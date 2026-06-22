# test_noise.py

import noise

print("START")
print("ENTER generate_base_terrain")
for i in range(100):
    for j in range(100):
        noise.pnoise2(
            i / 40.0,
            j / 40.0,
            octaves=6,
            persistence=0.5,
            lacunarity=2.0,
            repeatx=100,
            repeaty=100,
            base=42,
        )

print("DONE")