import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("orbital_dynamics")

# Hand-crafted high quality orbital mechanics documents
CORE_CONCEPTS = [
    {
        "id": "concept_hohmann",
        "text": """CONCEPT: Hohmann Transfer Orbit
DEFINITION: Most fuel-efficient method to transfer a spacecraft between two circular orbits using two engine burns.
FORMULA: Delta-v1 = sqrt(GM/r1) * (sqrt(2*r2/(r1+r2)) - 1)
FORMULA: Delta-v2 = sqrt(GM/r2) * (1 - sqrt(2*r1/(r1+r2)))
TRANSFER TIME: pi * sqrt((r1+r2)^3 / (8*GM))
EXAMPLE: Earth to Mars transfer takes ~259 days
RELATED: orbital transfer, delta-v, bi-elliptic transfer
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_kepler1",
        "text": """CONCEPT: Kepler's First Law
DEFINITION: Every planet orbits the Sun in an ellipse with the Sun at one focus.
FORMULA: r = a(1-e^2) / (1 + e*cos(theta))
WHERE: r=distance, a=semi-major axis, e=eccentricity, theta=true anomaly
IMPLICATION: Orbits are not circular — planets move faster near perihelion
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_kepler2",
        "text": """CONCEPT: Kepler's Second Law — Law of Equal Areas
DEFINITION: A line joining a planet to the Sun sweeps equal areas in equal times.
IMPLICATION: Planets move faster when closer to the Sun (perihelion) and slower when farther (aphelion)
RELATED: angular momentum conservation, orbital velocity
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_kepler3",
        "text": """CONCEPT: Kepler's Third Law — Harmonic Law
DEFINITION: The square of the orbital period is proportional to the cube of the semi-major axis.
FORMULA: T^2 = (4*pi^2 / GM) * a^3
SIMPLIFIED: T^2 proportional to a^3
EXAMPLE: Mars a=1.524 AU, T=1.881 years. Check: 1.524^3=3.54, 1.881^2=3.54 ✓
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_visviva",
        "text": """CONCEPT: Vis-Viva Equation
DEFINITION: Relates orbital speed to position in an orbit.
FORMULA: v^2 = GM * (2/r - 1/a)
WHERE: v=speed, G=gravitational constant, M=central body mass, r=current distance, a=semi-major axis
USE: Calculate orbital velocity at any point in an elliptical orbit
SPECIAL CASES: Circular orbit v=sqrt(GM/r), Escape velocity v=sqrt(2GM/r)
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_lagrange",
        "text": """CONCEPT: Lagrange Points
DEFINITION: Five positions in a two-body orbital system where a small object maintains stable position relative to both bodies.
L1: Between the two bodies — unstable, used for solar observation (SOHO, JWST)
L2: Beyond smaller body — unstable, used for space telescopes (James Webb)
L3: Opposite side of larger body — unstable
L4: 60 degrees ahead of smaller body — stable, Jupiter Trojans here
L5: 60 degrees behind smaller body — stable, Jupiter Trojans here
EXAMPLE: Jupiter has 1 million+ Trojan asteroids at L4 and L5
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_roche",
        "text": """CONCEPT: Roche Limit
DEFINITION: Minimum orbital distance at which tidal forces overcome self-gravity of a satellite, causing it to disintegrate.
FORMULA: d = R_M * (2 * rho_M / rho_m)^(1/3)
WHERE: R_M=primary radius, rho_M=primary density, rho_m=satellite density
EXAMPLE: Saturn's rings exist within the Roche limit
IMPLICATION: Moons cannot form inside the Roche limit
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_resonance",
        "text": """CONCEPT: Orbital Resonance
DEFINITION: When two orbiting bodies exert regular gravitational influence on each other due to orbital periods being related by ratio of small integers.
TYPES: Mean motion resonance (e.g. 2:1, 3:2), Spin-orbit resonance
EXAMPLES: 
- Jupiter-Saturn 5:2 near resonance
- Pluto-Neptune 3:2 resonance
- TRAPPIST-1 planets in chain resonance
- Io-Europa-Ganymede 4:2:1 resonance
EFFECT: Can stabilize or destabilize orbits
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_threebody",
        "text": """CONCEPT: Three-Body Problem
DEFINITION: Problem of determining motion of three mutually gravitating bodies. Has no general closed-form solution.
SPECIAL SOLUTIONS: Lagrange points, figure-8 choreography (Chenciner & Montgomery 2000)
CHAOS: Small changes in initial conditions lead to wildly different outcomes
RESTRICTED CASE: When one body has negligible mass (spacecraft in Earth-Moon system)
RELATED: N-body problem, chaos theory, orbital stability
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_eccentric",
        "text": """CONCEPT: Orbital Eccentricity
DEFINITION: Measure of how much an orbit deviates from a perfect circle. Ranges from 0 to 1 for bound orbits.
VALUES:
- e=0: Perfect circle
- 0 < e < 1: Ellipse
- e=1: Parabola (escape trajectory)
- e > 1: Hyperbola (unbound)
EXAMPLES: Earth e=0.017, Mars e=0.093, Halley's Comet e=0.967
FORMULA: e = sqrt(1 - (b/a)^2) where a=semi-major, b=semi-minor axis
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_escape",
        "text": """CONCEPT: Escape Velocity
DEFINITION: Minimum speed needed for an object to escape a gravitational field without further propulsion.
FORMULA: v_escape = sqrt(2GM/r)
EXAMPLES:
- Earth: 11.2 km/s
- Moon: 2.38 km/s
- Mars: 5.03 km/s
- Jupiter: 59.5 km/s
- Sun: 617.5 km/s
RELATED: orbital velocity, vis-viva equation
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "planet_mars",
        "text": """SOLAR SYSTEM PLANET: Mars
ORBITAL ELEMENTS:
Semi-major axis: 1.524 AU
Eccentricity: 0.0934
Inclination: 1.850 degrees
Orbital period: 686.97 days (1.881 years)
Perihelion: 1.381 AU
Aphelion: 1.666 AU
Average orbital speed: 24.07 km/s
Moons: Phobos (period 7.65h), Deimos (period 30.3h)
Hohmann transfer from Earth: ~259 days
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "planet_earth",
        "text": """SOLAR SYSTEM PLANET: Earth
ORBITAL ELEMENTS:
Semi-major axis: 1.000 AU
Eccentricity: 0.0167
Inclination: 0.000 degrees
Orbital period: 365.25 days
Perihelion: 0.983 AU (January)
Aphelion: 1.017 AU (July)
Average orbital speed: 29.78 km/s
Moon: Luna (period 27.32 days, distance 384,400 km)
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "planet_jupiter",
        "text": """SOLAR SYSTEM PLANET: Jupiter
ORBITAL ELEMENTS:
Semi-major axis: 5.203 AU
Eccentricity: 0.0489
Inclination: 1.304 degrees
Orbital period: 4332.59 days (11.86 years)
Average orbital speed: 13.07 km/s
Trojan asteroids: ~1 million at L4 and L5 Lagrange points
Moons: 95 known, including Io Europa Ganymede Callisto (Galilean moons)
Io-Europa-Ganymede in 4:2:1 orbital resonance
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "planet_saturn",
        "text": """SOLAR SYSTEM PLANET: Saturn
ORBITAL ELEMENTS:
Semi-major axis: 9.537 AU
Eccentricity: 0.0565
Inclination: 2.485 degrees
Orbital period: 10759.22 days (29.46 years)
Average orbital speed: 9.68 km/s
Ring system: exists within Roche limit, extends to 282,000 km
Cassini Division: caused by 2:1 resonance with Mimas
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_gravity_assist",
        "text": """CONCEPT: Gravity Assist / Gravitational Slingshot
DEFINITION: Spacecraft uses planet's gravity and orbital motion to gain speed without using fuel.
HOW IT WORKS: Spacecraft approaches planet, swings around it, exits faster relative to Sun
FORMULA: delta_v = 2 * V_planet * sin(turning_angle/2)
EXAMPLES:
- Voyager 1 and 2 used Jupiter and Saturn gravity assists
- Cassini used Venus twice, Earth, Jupiter before reaching Saturn
- New Horizons used Jupiter assist to reach Pluto faster
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_tidal_locking",
        "text": """CONCEPT: Tidal Locking
DEFINITION: When a body's rotation period equals its orbital period, causing same face to always point toward primary.
CAUSE: Tidal forces dissipate rotational energy until synchronous rotation achieved
EXAMPLES:
- Moon is tidally locked to Earth
- Mercury in 3:2 spin-orbit resonance with Sun
- Most large moons in solar system are tidally locked
TIMESCALE: Depends on body size, distance, and composition
DOMAIN: orbital_dynamics"""
    },
    {
        "id": "concept_perturbation",
        "text": """CONCEPT: Orbital Perturbation
DEFINITION: Deviation from pure two-body Keplerian orbit due to additional gravitational influences.
SOURCES: Other planets, non-spherical mass distribution, atmospheric drag, radiation pressure
EFFECTS: Precession of perihelion, nodal regression, orbital decay
FAMOUS EXAMPLE: Precession of Mercury's perihelion (43 arcsec/century) explained by General Relativity
METHODS: Lagrange planetary equations, numerical integration
DOMAIN: orbital_dynamics"""
    }
]

print(f"Adding {len(CORE_CONCEPTS)} core orbital mechanics concepts...")

collection.add(
    documents=[c["text"] for c in CORE_CONCEPTS],
    metadatas=[{"source": "curated", "type": "concept"} for c in CORE_CONCEPTS],
    ids=[c["id"] for c in CORE_CONCEPTS]
)

print(f"Total documents now: {collection.count()}")
print("\nTesting Mars query...")
r = collection.query(query_texts=["Mars orbital period eccentricity"], n_results=2)
for i, doc in enumerate(r["documents"][0]):
    print(f"\nResult {i+1}:")
    print(doc[:300])

print("\nTesting Hohmann transfer...")
r = collection.query(query_texts=["Hohmann transfer orbit delta-v"], n_results=2)
for i, doc in enumerate(r["documents"][0]):
    print(f"\nResult {i+1}:")
    print(doc[:300])