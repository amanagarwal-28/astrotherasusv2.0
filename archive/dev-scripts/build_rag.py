import json
import csv
import os
import chromadb

print("=" * 50)
print("ASTRO THESAURUS — RAG DATABASE BUILDER")
print("Domain: Orbital Dynamics Only")
print("=" * 50)

# Initialize ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Delete existing collection if rebuilding
try:
    client.delete_collection("orbital_dynamics")
    print("Cleared existing database")
except:
    pass

collection = client.create_collection(
    name="orbital_dynamics",
    metadata={"description": "Orbital mechanics and dynamics knowledge base"}
)

documents = []
metadatas = []
ids = []
doc_id = 0

# ── DATASET 1: UAT Concepts ──────────────────────────────────
# ── DATASET 1: UAT Concepts (FIXED) ──────────────────────────
print("\n[1/7] Processing UAT.json...")
try:
    with open("datasets/UAT.json", "r", encoding="utf-8") as f:
        uat_data = json.load(f)

    def flatten_uat(nodes, results):
        for node in nodes:
            name = node.get("name", "")
            definition = node.get("definition") or ""
            # Only keep it if it's related to orbital dynamics
            if any(k in name.lower() for k in ["orbit", "dynamics", "kepler", "gravity"]):
                results.append(f"CONCEPT: {name}\nDEFINITION: {definition}\nDOMAIN: orbital_dynamics")
            if "children" in node and node["children"]:
                flatten_uat(node["children"], results)

    uat_docs = []
    flatten_uat(uat_data.get("children", []), uat_docs)
    
    for i, doc in enumerate(uat_docs):
        documents.append(doc)
        metadatas.append({"source": "UAT", "type": "thesaurus"})
        ids.append(f"uat_{i}")
    
    print(f"    Added {len(uat_docs)} orbital dynamics concepts from UAT")
except Exception as e:
    print(f"    Error: {e}")

# ── DATASET 2: Exoplanets ────────────────────────────────────
print("\n[2/7] Processing exoplanets.csv...")
try:
    exo_count = 0
    with open("datasets/exoplanets.csv", "r", encoding="utf-8") as f:
        # Skip comment lines starting with #
        lines = [l for l in f if not l.startswith("#")]

    reader = csv.DictReader(lines)
    batch = []

    for row in reader:
        name = row.get("pl_name", "").strip()
        if not name:
            continue

        a = row.get("pl_orbsmax", "").strip()
        e = row.get("pl_orbeccen", "").strip()
        mass = row.get("pl_bmassj", "").strip()
        radius = row.get("pl_rade", "").strip()
        host = row.get("hostname", "").strip()
        teff = row.get("st_teff", "").strip()

        doc_text = f"EXOPLANET: {name}\n"
        doc_text += f"HOST STAR: {host}\n"
        if a: doc_text += f"SEMI-MAJOR AXIS: {a} AU\n"
        if e: doc_text += f"ECCENTRICITY: {e}\n"
        if mass: doc_text += f"MASS: {mass} Jupiter masses\n"
        if radius: doc_text += f"RADIUS: {radius} Earth radii\n"
        if teff: doc_text += f"HOST STAR TEMPERATURE: {teff} K\n"

        # Classify type
        try:
            a_val = float(a) if a else None
            m_val = float(mass) if mass else None
            if a_val and a_val < 0.1 and m_val and m_val > 0.3:
                doc_text += "TYPE: Hot Jupiter — gas giant in close orbit\n"
            elif m_val and m_val < 0.1:
                doc_text += "TYPE: Super Earth or Neptune-sized planet\n"
            elif a_val and 0.95 < a_val < 1.37:
                doc_text += "TYPE: Potentially in habitable zone\n"
        except:
            pass

        doc_text += "DOMAIN: orbital_dynamics\n"
        batch.append((doc_text, {"source": "NASA_exoplanet", "planet": name, "type": "exoplanet"}, f"exo_{doc_id}"))
        doc_id += 1
        exo_count += 1

        # Add in batches of 500
        if len(batch) >= 500:
            collection.add(
                documents=[b[0] for b in batch],
                metadatas=[b[1] for b in batch],
                ids=[b[2] for b in batch]
            )
            batch = []

    if batch:
        documents_batch = [b[0] for b in batch]
        metadatas_batch = [b[1] for b in batch]
        ids_batch = [b[2] for b in batch]
        collection.add(documents=documents_batch, metadatas=metadatas_batch, ids=ids_batch)

    print(f"    Added {exo_count} exoplanets")

except Exception as e:
    print(f"    Error: {e}")

# ── DATASET 3: Planets (Horizons) ────────────────────────────
print("\n[3/7] Processing planets_horizons.json...")
try:
    with open("datasets/planets_horizons.json", "r", encoding="utf-8") as f:
        planets_data = json.load(f)

    planet_count = 0
    for planet_name, data in planets_data.items():
        result_text = data.get("result", "")

        doc_text = f"SOLAR SYSTEM BODY: {planet_name.title()}\n"
        doc_text += f"DATA SOURCE: NASA JPL Horizons\n"
        doc_text += f"RAW DATA: {result_text[:800]}\n"
        doc_text += "DOMAIN: orbital_dynamics\n"

        documents.append(doc_text)
        metadatas.append({"source": "JPL_Horizons", "body": planet_name, "type": "planet"})
        ids.append(f"planet_{doc_id}")
        doc_id += 1
        planet_count += 1

    print(f"    Added {planet_count} planets")

except Exception as e:
    print(f"    Error: {e}")

# ── DATASET 4: Asteroids ─────────────────────────────────────
print("\n[4/7] Processing asteroids.json...")
try:
    with open("datasets/asteroids.json", "r", encoding="utf-8") as f:
        ast_data = json.load(f)

    fields = ast_data.get("fields", [])
    data_rows = ast_data.get("data", [])
    ast_count = 0

    for row in data_rows[:1000]:
        if len(row) != len(fields):
            continue
        obj = dict(zip(fields, row))
        name = obj.get("full_name", "Unknown")

        doc_text = f"ASTEROID: {name}\n"
        for field in ["a", "e", "i", "per", "moid", "class"]:
            if obj.get(field):
                labels = {
                    "a": "Semi-major axis (AU)",
                    "e": "Eccentricity",
                    "i": "Inclination (deg)",
                    "per": "Orbital period (days)",
                    "moid": "Min orbit intersection distance (AU)",
                    "class": "Orbital class"
                }
                doc_text += f"{labels[field]}: {obj[field]}\n"
        doc_text += "DOMAIN: orbital_dynamics\n"

        documents.append(doc_text)
        metadatas.append({"source": "JPL_SBDB", "body": name, "type": "asteroid"})
        ids.append(f"ast_{doc_id}")
        doc_id += 1
        ast_count += 1

    print(f"    Added {ast_count} asteroids")

except Exception as e:
    print(f"    Error: {e}")

# ── DATASET 5: Small Bodies ──────────────────────────────────
print("\n[5/7] Processing small_body.json...")
try:
    with open("datasets/small_body.json", "r", encoding="utf-8") as f:
        sb_data = json.load(f)

    fields = sb_data.get("fields", [])
    data_rows = sb_data.get("data", [])
    sb_count = 0

    for row in data_rows[:1000]:
        if len(row) != len(fields):
            continue
        obj = dict(zip(fields, row))
        name = obj.get("full_name", "Unknown")

        doc_text = f"SMALL BODY: {name}\n"
        for field in ["a", "e", "i", "per", "moid", "class"]:
            if obj.get(field):
                labels = {
                    "a": "Semi-major axis (AU)",
                    "e": "Eccentricity",
                    "i": "Inclination (deg)",
                    "per": "Orbital period (days)",
                    "moid": "Min orbit intersection distance",
                    "class": "Object class"
                }
                doc_text += f"{labels[field]}: {obj[field]}\n"
        doc_text += "DOMAIN: orbital_dynamics\n"

        documents.append(doc_text)
        metadatas.append({"source": "JPL_SBDB", "body": name, "type": "small_body"})
        ids.append(f"sb_{doc_id}")
        doc_id += 1
        sb_count += 1

    print(f"    Added {sb_count} small bodies")

except Exception as e:
    print(f"    Error: {e}")

# ── DATASET 6: Trojans ───────────────────────────────────────
print("\n[6/7] Processing trojan.json...")
try:
    with open("datasets/trojan.json", "r", encoding="utf-8") as f:
        tj_data = json.load(f)

    fields = tj_data.get("fields", [])
    data_rows = tj_data.get("data", [])
    tj_count = 0

    for row in data_rows:
        if len(row) != len(fields):
            continue
        obj = dict(zip(fields, row))
        name = obj.get("full_name", "Unknown")

        doc_text = f"JUPITER TROJAN ASTEROID: {name}\n"
        doc_text += "ORBITAL TYPE: Trojan — librates around L4 or L5 Lagrange point\n"
        for field in ["a", "e", "i", "per"]:
            if obj.get(field):
                labels = {"a":"Semi-major axis (AU)","e":"Eccentricity","i":"Inclination (deg)","per":"Period (days)"}
                doc_text += f"{labels[field]}: {obj[field]}\n"
        doc_text += "DOMAIN: orbital_dynamics\n"

        documents.append(doc_text)
        metadatas.append({"source": "JPL_SBDB", "body": name, "type": "trojan"})
        ids.append(f"tj_{doc_id}")
        doc_id += 1
        tj_count += 1

    print(f"    Added {tj_count} Trojan asteroids")

except Exception as e:
    print(f"    Error: {e}")

# ── DATASET 7: Comets ────────────────────────────────────────
print("\n[7/7] Processing comet.json...")
try:
    with open("datasets/comet.json", "r", encoding="utf-8") as f:
        cm_data = json.load(f)

    fields = cm_data.get("fields", [])
    data_rows = cm_data.get("data", [])
    cm_count = 0

    for row in data_rows:
        if len(row) != len(fields):
            continue
        obj = dict(zip(fields, row))
        name = obj.get("full_name", "Unknown")

        doc_text = f"COMET: {name}\n"
        doc_text += "OBJECT TYPE: Comet — icy small body with highly eccentric orbit\n"
        for field in ["a", "e", "i", "per", "class"]:
            if obj.get(field):
                labels = {"a":"Semi-major axis (AU)","e":"Eccentricity","i":"Inclination (deg)","per":"Period (days)","class":"Comet class"}
                doc_text += f"{labels[field]}: {obj[field]}\n"
        doc_text += "DOMAIN: orbital_dynamics\n"

        documents.append(doc_text)
        metadatas.append({"source": "JPL_SBDB", "body": name, "type": "comet"})
        ids.append(f"cm_{doc_id}")
        doc_id += 1
        cm_count += 1

    print(f"    Added {cm_count} comets")

except Exception as e:
    print(f"    Error: {e}")

# ── ADD ALL REMAINING DOCS TO CHROMADB ───────────────────────
print("\nAdding all documents to ChromaDB...")
BATCH_SIZE = 500
for i in range(0, len(documents), BATCH_SIZE):
    collection.add(
        documents=documents[i:i+BATCH_SIZE],
        metadatas=metadatas[i:i+BATCH_SIZE],
        ids=ids[i:i+BATCH_SIZE]
    )
    print(f"    Inserted {min(i+BATCH_SIZE, len(documents))}/{len(documents)} documents...")

# ── SUMMARY ──────────────────────────────────────────────────
total = collection.count()
print("\n" + "=" * 50)
print("RAG DATABASE BUILT SUCCESSFULLY!")
print(f"Total documents in database: {total}")
print(f"Database location: ./chroma_db/")
print("=" * 50)

# ── TEST QUERY ───────────────────────────────────────────────
print("\nRunning test query: 'Mars orbital period eccentricity'")
results = collection.query(
    query_texts=["Mars orbital period eccentricity"],
    n_results=3
)
for i, doc in enumerate(results["documents"][0]):
    print(f"\nResult {i+1}:")
    print(doc[:200])
