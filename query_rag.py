import chromadb

# Connect to existing database
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("orbital_dynamics")

ORBITAL_KEYWORDS = [
    "orbit", "orbital", "planet", "star", "comet", "asteroid",
    "kepler", "gravity", "trajectory", "ellipse", "perihelion",
    "aphelion", "eccentricity", "inclination", "resonance",
    "lagrange", "transfer", "hohmann", "tidal", "binary",
    "moon", "satellite", "ephemeris", "conjunction", "transit",
    "roche", "retrograde", "prograde", "semi-major", "exoplanet",
    "solar system", "mars", "earth", "jupiter", "saturn", "venus",
    "mercury", "uranus", "neptune", "simulate", "simulation"
]

def is_orbital_query(text):
    """Check if query is related to orbital dynamics"""
    text = text.lower()
    return any(kw in text for kw in ORBITAL_KEYWORDS)

def query_rag(user_question, n_results=3):
    """
    Search RAG database and return relevant context
    Returns: string of relevant documents joined together
    """
    if not is_orbital_query(user_question):
        return None  # Outside our domain

    try:
        results = collection.query(
            query_texts=[user_question],
            n_results=n_results
        )
        docs = results["documents"][0]
        context = "\n\n---\n\n".join(docs)
        return context

    except Exception as e:
        print(f"RAG query error: {e}")
        return None

def query_rag_by_type(user_question, doc_type, n_results=3):
    """
    Search RAG database filtered by document type
    doc_type: 'planet', 'concept', 'exoplanet', 'asteroid', 'comet', 'trojan'
    """
    try:
        results = collection.query(
            query_texts=[user_question],
            n_results=n_results,
            where={"type": doc_type}
        )
        docs = results["documents"][0]
        return "\n\n---\n\n".join(docs)
    except Exception as e:
        print(f"RAG filtered query error: {e}")
        return None

def query_rag_multi(user_question):
    """
    Smart query — searches multiple types and combines best results
    Used for complex questions that need both concept + data
    """
    results = []

    # Always get concept definitions
    concept = query_rag_by_type(user_question, "concept", n_results=2)
    if concept:
        results.append("DEFINITIONS:\n" + concept)

    # Get planet data if planet mentioned
    planets = ["mars", "earth", "jupiter", "saturn", "venus",
               "mercury", "uranus", "neptune"]
    for planet in planets:
        if planet in user_question.lower():
            planet_data = query_rag_by_type(
                user_question, "planet", n_results=1
            )
            if planet_data:
                results.append("PLANET DATA:\n" + planet_data)
            break

    # Get exoplanet data if relevant
    if any(w in user_question.lower() for w in
           ["exoplanet", "hot jupiter", "super earth", "extrasolar"]):
        exo = query_rag_by_type(user_question, "exoplanet", n_results=2)
        if exo:
            results.append("EXOPLANET DATA:\n" + exo)

    # Get comet data if relevant
    if any(w in user_question.lower() for w in
           ["comet", "halley", "eccentric", "icy"]):
        comet = query_rag_by_type(user_question, "comet", n_results=2)
        if comet:
            results.append("COMET DATA:\n" + comet)

    # Fallback to general search if nothing found
    if not results:
        general = query_rag(user_question, n_results=3)
        if general:
            results.append(general)

    return "\n\n".join(results) if results else None

# ── TEST ──────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "What is Mars orbital period and eccentricity?",
        "How does Hohmann transfer work?",
        "Show me hot Jupiter exoplanets",
        "What are Lagrange points?",
        "Explain Kepler third law",
        "What is the weather like today?"  # Should be rejected
    ]

    for q in tests:
        print(f"\nQ: {q}")
        if not is_orbital_query(q):
            print("REJECTED — outside orbital dynamics domain")
            continue
        result = query_rag_multi(q)
        if result:
            print(result[:300])
        print("-" * 50)