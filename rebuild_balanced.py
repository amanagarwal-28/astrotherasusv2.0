import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

# Delete and recreate
try:
    client.delete_collection("orbital_dynamics")
    print("Cleared old database")
except:
    pass

collection = client.create_collection("orbital_dynamics")

import json, csv

documents = []
metadatas = []
ids = []

# ── CURATED CONCEPTS (highest priority) ──────────────────────
CONCEPTS = [
    ("concept_mars", "SOLAR SYSTEM PLANET: Mars\nSemi-major axis: 1.524 AU\nEccentricity: 0.0934\nOrbital period: 686.97 days\nPerihelion: 1.381 AU\nAphelion: 1.666 AU\nSpeed: 24.07 km/s\nHohmann transfer from Earth: 259 days\nDOMAIN: orbital_dynamics", "planet"),
    ("concept_earth", "SOLAR SYSTEM PLANET: Earth\nSemi-major axis: 1.000 AU\nEccentricity: 0.0167\nOrbital period: 365.25 days\nSpeed: 29.78 km/s\nMoon distance: 384400 km\nDOMAIN: orbital_dynamics", "planet"),
    ("concept_venus", "SOLAR SYSTEM PLANET: Venus\nSemi-major axis: 0.723 AU\nEccentricity: 0.0067\nOrbital period: 224.70 days\nSpeed: 35.02 km/s\nDOMAIN: orbital_dynamics", "planet"),
    ("concept_mercury", "SOLAR SYSTEM PLANET: Mercury\nSemi-major axis: 0.387 AU\nEccentricity: 0.2056\nOrbital period: 87.97 days\nSpeed: 47.36 km/s\nPerihelion precession: 43 arcsec/century explained by GR\nDOMAIN: orbital_dynamics", "planet"),
    ("concept_jupiter", "SOLAR SYSTEM PLANET: Jupiter\nSemi-major axis: 5.203 AU\nEccentricity: 0.0489\nOrbital period: 4332.59 days\nSpeed: 13.07 km/s\nTrojan asteroids at L4 L5\nIo Europa Ganymede in 4:2:1 resonance\nDOMAIN: orbital_dynamics", "planet"),
    ("concept_saturn", "SOLAR SYSTEM PLANET: Saturn\nSemi-major axis: 9.537 AU\nEccentricity: 0.0565\nOrbital period: 10759 days\nRings within Roche limit\nCassini Division from 2:1 resonance with Mimas\nDOMAIN: orbital_dynamics", "planet"),
    ("concept_uranus", "SOLAR SYSTEM PLANET: Uranus\nSemi-major axis: 19.19 AU\nEccentricity: 0.0457\nOrbital period: 30688 days\nAxial tilt: 97.77 degrees\nDOMAIN: orbital_dynamics", "planet"),
    ("concept_neptune", "SOLAR SYSTEM PLANET: Neptune\nSemi-major axis: 30.07 AU\nEccentricity: 0.0113\nOrbital period: 60182 days\nPluto in 3:2 resonance with Neptune\nDOMAIN: orbital_dynamics", "planet"),
    ("concept_hohmann", "CONCEPT: Hohmann Transfer Orbit\nDEFINITION: Most fuel efficient orbital transfer between two circular orbits using two burns\nFORMULA: delta_v1 = sqrt(GM/r1)*(sqrt(2*r2/(r1+r2))-1)\nFORMULA: delta_v2 = sqrt(GM/r2)*(1-sqrt(2*r1/(r1+r2)))\nTRANSFER TIME: pi*sqrt((r1+r2)^3/(8*GM))\nEXAMPLE: Earth to Mars 259 days\nRELATED: delta-v orbital transfer spacecraft\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_kepler1", "CONCEPT: Kepler First Law\nEvery planet orbits the Sun in an ellipse with Sun at one focus\nFORMULA: r = a(1-e^2)/(1+e*cos(theta))\nPerihelion: closest point, fastest speed\nAphelion: farthest point, slowest speed\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_kepler2", "CONCEPT: Kepler Second Law Equal Areas\nA line joining planet to Sun sweeps equal areas in equal times\nConservation of angular momentum\nPlanets move faster at perihelion slower at aphelion\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_kepler3", "CONCEPT: Kepler Third Law Harmonic\nT^2 proportional to a^3\nFORMULA: T^2 = (4*pi^2/GM)*a^3\nEXAMPLE: Mars a=1.524 AU T=1.881 years check: 1.524^3=3.54 1.881^2=3.54\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_visviva", "CONCEPT: Vis-Viva Equation\nFORMULA: v^2 = GM*(2/r - 1/a)\nv=orbital speed r=current distance a=semi-major axis\nCircular orbit: v=sqrt(GM/r)\nEscape velocity: v=sqrt(2GM/r)\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_lagrange", "CONCEPT: Lagrange Points L1 L2 L3 L4 L5\nFive positions where small body stays stable relative to two large bodies\nL1: between bodies unstable SOHO spacecraft here\nL2: beyond small body unstable James Webb Space Telescope here\nL3: opposite side unstable\nL4: 60 degrees ahead stable Jupiter Trojans\nL5: 60 degrees behind stable Jupiter Trojans\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_roche", "CONCEPT: Roche Limit\nMinimum distance where tidal forces overcome self-gravity\nFORMULA: d = R_M*(2*rho_M/rho_m)^(1/3)\nSaturn rings exist within Roche limit\nMoons cannot form inside Roche limit\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_resonance", "CONCEPT: Orbital Resonance Mean Motion\nTwo bodies exert regular gravitational influence when periods are integer ratios\nEXAMPLES: Pluto Neptune 3:2, Io Europa Ganymede 4:2:1, TRAPPIST-1 chain\nCan stabilize or destabilize orbits\nKirkwood gaps in asteroid belt from Jupiter resonances\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_threebody", "CONCEPT: Three Body Problem N-body\nNo general closed-form solution for three mutually gravitating bodies\nSpecial solutions: Lagrange points figure-8 choreography\nChaotic sensitive to initial conditions\nRestricted three body: spacecraft in Earth-Moon system\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_eccentricity", "CONCEPT: Orbital Eccentricity\ne=0 circle, 0<e<1 ellipse, e=1 parabola, e>1 hyperbola\nEXAMPLES: Earth 0.017 Mars 0.093 Pluto 0.248 Halley comet 0.967\nFORMULA: e=sqrt(1-(b/a)^2)\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_escape", "CONCEPT: Escape Velocity\nFORMULA: v=sqrt(2GM/r)\nEarth: 11.2 km/s Moon: 2.38 km/s Mars: 5.03 km/s Jupiter: 59.5 km/s\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_gravity_assist", "CONCEPT: Gravity Assist Gravitational Slingshot\nSpacecraft uses planet orbital motion to gain speed\nFORMULA: delta_v = 2*V_planet*sin(turning_angle/2)\nVoyager used Jupiter Saturn assist\nCassini used Venus Venus Earth Jupiter before Saturn\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_tidal", "CONCEPT: Tidal Locking Synchronous Rotation\nRotation period equals orbital period same face always toward primary\nMoon tidally locked to Earth\nMercury in 3:2 spin-orbit resonance\nMost large moons tidally locked\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_perturbation", "CONCEPT: Orbital Perturbation\nDeviation from Keplerian orbit due to additional gravity\nSources: other planets non-spherical bodies atmospheric drag radiation\nMercury perihelion precession 43 arcsec/century from General Relativity\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_binary", "CONCEPT: Binary Star System\nTwo stars orbiting common center of mass barycenter\nCLASSES: visual spectroscopic eclipsing contact\nOrbital period from hours to thousands of years\nMass ratio determines barycenter position\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_inclination", "CONCEPT: Orbital Inclination\nAngle between orbital plane and reference plane\nPrograde: inclination less than 90 degrees\nRetrograde: inclination greater than 90 degrees\nEarth equatorial plane reference for satellites\nEcliptic plane reference for solar system\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_semimajor", "CONCEPT: Semi-Major Axis\nHalf the longest diameter of elliptical orbit\nDetermines orbital period via Kepler third law\nAverage of perihelion and aphelion distances\na = (perihelion + aphelion) / 2\nDOMAIN: orbital_dynamics", "concept"),
    ("concept_halley", "COMET: Halley Comet\nOrbital period: 75-76 years\nSemi-major axis: 17.8 AU\nEccentricity: 0.967\nPerihelion: 0.586 AU inside Venus orbit\nAphelion: 35 AU beyond Neptune\nLast perihelion: 1986 Next: 2061\nDOMAIN: orbital_dynamics", "comet"),
]

for cid, text, ctype in CONCEPTS:
    documents.append(text)
    metadatas.append({"source": "curated", "type": ctype})
    ids.append(cid)

print(f"Added {len(CONCEPTS)} curated concepts")

# ── EXOPLANETS (500 only, best ones) ─────────────────────────
print("Adding exoplanets...")
exo_count = 0
try:
    with open("datasets/exoplanets.csv", "r", encoding="utf-8") as f:
        lines = [l for l in f if not l.startswith("#")]
    for row in csv.DictReader(lines):
        if exo_count >= 500:
            break
        name = row.get("pl_name", "").strip()
        a    = row.get("pl_orbsmax", "").strip()
        e    = row.get("pl_orbeccen", "").strip()
        mass = row.get("pl_bmassj", "").strip()
        host = row.get("hostname", "").strip()
        if not name or not a:
            continue
        doc = f"EXOPLANET: {name}\nHOST: {host}\nSEMI-MAJOR AXIS: {a} AU\nECCENTRICITY: {e}\nMASS: {mass} Mjup\nDOMAIN: orbital_dynamics"
        documents.append(doc)
        metadatas.append({"source": "NASA", "type": "exoplanet"})
        ids.append(f"exo_{exo_count}")
        exo_count += 1
    print(f"    Added {exo_count} exoplanets")
except Exception as e:
    print(f"    Error: {e}")

# ── ASTEROIDS (100 only, famous ones first) ───────────────────
print("Adding asteroids...")
ast_count = 0
try:
    with open("datasets/asteroids.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    fields = data.get("fields", [])
    for row in data.get("data", [])[:100]:
        if len(row) != len(fields):
            continue
        obj = dict(zip(fields, row))
        name = obj.get("full_name", "")
        doc = f"ASTEROID: {name}\nSemi-major axis: {obj.get('a','')} AU\nEccentricity: {obj.get('e','')}\nPeriod: {obj.get('per','')} days\nClass: {obj.get('class','')}\nDOMAIN: orbital_dynamics"
        documents.append(doc)
        metadatas.append({"source": "JPL", "type": "asteroid"})
        ids.append(f"ast_{ast_count}")
        ast_count += 1
    print(f"    Added {ast_count} asteroids")
except Exception as e:
    print(f"    Error: {e}")

# ── TROJANS (100 only) ────────────────────────────────────────
print("Adding Trojans...")
tj_count = 0
try:
    with open("datasets/trojan.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    fields = data.get("fields", [])
    for row in data.get("data", [])[:100]:
        if len(row) != len(fields):
            continue
        obj = dict(zip(fields, row))
        name = obj.get("full_name", "")
        doc = f"JUPITER TROJAN: {name}\nAt L4 or L5 Lagrange point\nSemi-major axis: {obj.get('a','')} AU\nEccentricity: {obj.get('e','')}\nDOMAIN: orbital_dynamics"
        documents.append(doc)
        metadatas.append({"source": "JPL", "type": "trojan"})
        ids.append(f"tj_{tj_count}")
        tj_count += 1
    print(f"    Added {tj_count} Trojans")
except Exception as e:
    print(f"    Error: {e}")

# ── COMETS (all ~500) ─────────────────────────────────────────
print("Adding comets...")
cm_count = 0
try:
    with open("datasets/comet.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    fields = data.get("fields", [])
    for row in data.get("data", []):
        if len(row) != len(fields):
            continue
        obj = dict(zip(fields, row))
        name = obj.get("full_name", "")
        doc = f"COMET: {name}\nEccentricity: {obj.get('e','')} (highly eccentric)\nSemi-major axis: {obj.get('a','')} AU\nPeriod: {obj.get('per','')} days\nDOMAIN: orbital_dynamics"
        documents.append(doc)
        metadatas.append({"source": "JPL", "type": "comet"})
        ids.append(f"cm_{cm_count}")
        cm_count += 1
    print(f"    Added {cm_count} comets")
except Exception as e:
    print(f"    Error: {e}")

# ── INSERT ALL ────────────────────────────────────────────────
print(f"\nInserting {len(documents)} documents...")
BATCH = 200
for i in range(0, len(documents), BATCH):
    collection.add(
        documents=documents[i:i+BATCH],
        metadatas=metadatas[i:i+BATCH],
        ids=ids[i:i+BATCH]
    )

print(f"\nTotal: {collection.count()} documents")

# ── TEST ──────────────────────────────────────────────────────
tests = [
    "Mars orbital period eccentricity",
    "Hohmann transfer orbit delta-v",
    "Lagrange points L4 L5 trojan",
    "Kepler third law period semi-major axis",
    "escape velocity formula"
]

for query in tests:
    print(f"\nQUERY: {query}")
    r = collection.query(query_texts=[query], n_results=1)
    print(r["documents"][0][0][:200])
    print("-"*40)