import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("orbital_dynamics")

print(f"Total documents: {collection.count()}")
print("\n" + "="*50)

# Test 1 - Search for Mars specifically
print("TEST 1: Mars")
r = collection.query(query_texts=["Mars planet solar system orbit"], n_results=3)
for i, doc in enumerate(r["documents"][0]):
    print(f"\nResult {i+1}:")
    print(doc[:300])

print("\n" + "="*50)

# Test 2 - Lagrange points
print("TEST 2: Lagrange points")
r = collection.query(query_texts=["Lagrange points L4 L5 trojan"], n_results=3)
for i, doc in enumerate(r["documents"][0]):
    print(f"\nResult {i+1}:")
    print(doc[:300])

print("\n" + "="*50)

# Test 3 - Hohmann transfer
print("TEST 3: Hohmann transfer orbit")
r = collection.query(query_texts=["Hohmann transfer orbit delta-v"], n_results=3)
for i, doc in enumerate(r["documents"][0]):
    print(f"\nResult {i+1}:")
    print(doc[:300])

print("\n" + "="*50)

# Test 4 - Hot Jupiter
print("TEST 4: Hot Jupiter exoplanet")
r = collection.query(query_texts=["hot jupiter exoplanet close orbit"], n_results=3)
for i, doc in enumerate(r["documents"][0]):
    print(f"\nResult {i+1}:")
    print(doc[:300])