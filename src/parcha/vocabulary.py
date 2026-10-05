"""Domain vocabulary used by the verbatim workshop-intake pass."""

# Prisma accepts individual words in its bias list. Keep compound workshop terms as
# their constituent words so the request remains valid at the API boundary.
AUTOMOTIVE_BIAS_WORDS: tuple[str, ...] = (
    "activa", "alternator", "axle", "battery", "bearing", "belt", "brake",
    "caliper", "camshaft", "carburetor", "chain", "clutch", "coil", "coolant",
    "crankshaft", "disc", "drum", "engine", "filter", "fork", "fuel", "fuse",
    "gear", "gasket", "grease", "handlebar", "headlight", "hose", "injector",
    "lever", "mobil", "motor", "oil", "pad", "piston", "plug", "radiator",
    "ring", "rotor", "scooter", "seal", "sensor", "shocker", "shoe", "silencer",
    "spark", "sprocket", "starter", "suspension", "throttle", "timing", "tire",
    "tube", "tuning", "valve", "wheel", "wire", "workshop", "Honda", "Bajaj",
    "Hero", "Maruti", "Suzuki", "TVS", "Yamaha",
)
