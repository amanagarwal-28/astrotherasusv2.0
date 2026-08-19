import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("orbital_dynamics")

# Delete old Mars entry and re-add with stronger keywords
try:
    collection.delete(ids=["concept_mars"])
except:
    pass

collection.add(
    documents=["""SOLAR SYSTEM PLANET: Mars Mars Mars
orbital period: 686.97 days
eccentricity: 0.0934
semi-major axis: 1.524 AU
perihelion: 1.381 AU
aphelion: 1.666 AU
orbital speed: 24.07 km/s
Mars orbit simulation
Mars trajectory
Hohmann transfer Earth to Mars: 259 days
DOMAIN: orbital_dynamics"""],
    metadatas=[{"source": "curated", "type": "planet"}],
    ids=["concept_mars"]
)

# Test all 5 queries
tests = [
    "Mars orbital period eccentricity",
    "Hohmann transfer orbit delta-v",
    "Lagrange points L4 L5",
    "Kepler third law",
    "escape velocity"
]

for q in tests:
    r = collection.query(query_texts=[q], n_results=1)
    print(f"\nQ: {q}")
    print(r["documents"][0][0][:150])
    print("-"*40)