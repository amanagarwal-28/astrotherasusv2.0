import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"  

def ask_ollama(prompt, system=None):
    """Send a prompt to Ollama and get response"""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low = more consistent output
                    "num_predict": 500
                }
            },
            timeout=120
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Ollama error: {e}"

def parse_intent(user_input):
    """
    Use Ollama to parse user input into structured intent
    Returns a dict with intent, body, action, duration
    """
    system = """You are an orbital mechanics assistant parser.
Convert user input into JSON. Reply with ONLY valid JSON, nothing else.

JSON structure:
{
  "intent": "simulate|query|explain|plot|compare",
  "body": "planet or object name in lowercase or null",
  "action": "orbit|transfer|lagrange|resonance|flyby|explain|list",
  "duration_days": number or null,
  "reference": "sun|earth|jupiter or null",
  "plot_type": "orbit|histogram|phase|hr|trajectory or null",
  "is_orbital": true or false
}

Examples:
Input: "Simulate Mars orbit for 2 years"
Output: {"intent":"simulate","body":"mars","action":"orbit","duration_days":730,"reference":"sun","plot_type":"orbit","is_orbital":true}

Input: "What is a Hohmann transfer?"
Output: {"intent":"explain","body":null,"action":"transfer","duration_days":null,"reference":null,"plot_type":null,"is_orbital":true}

Input: "Show Earth to Mars transfer orbit"
Output: {"intent":"plot","body":"mars","action":"transfer","duration_days":259,"reference":"earth","plot_type":"trajectory","is_orbital":true}

Input: "What is the best pizza topping?"
Output: {"intent":"unknown","body":null,"action":null,"duration_days":null,"reference":null,"plot_type":null,"is_orbital":false}
"""

    response = ask_ollama(user_input, system=system)

    # Clean response — remove markdown if present
    response = response.replace("```json", "").replace("```", "").strip()

    # Find JSON in response
    try:
        # Try direct parse first
        return json.loads(response)
    except:
        # Try to extract JSON from response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(response[start:end])
            except:
                pass

    # Fallback if parsing fails
    return {
        "intent": "unknown",
        "body": None,
        "action": None,
        "duration_days": None,
        "reference": None,
        "plot_type": None,
        "is_orbital": False
    }

def build_rag_prompt(user_question, rag_context):
    """
    Build the final prompt that combines RAG context + user question
    This is what gets sent to Ollama for the actual answer
    """
    return f"""You are an expert in orbital mechanics and astronomy.
Use ONLY the following data to answer the question.
Be specific — use exact numbers from the data.
Keep answer under 150 words.
If the data doesn't contain the answer, say "I don't have that data."

REFERENCE DATA:
{rag_context}

QUESTION: {user_question}

ANSWER:"""

def answer_with_rag(user_question, rag_context):
    """Full RAG-augmented answer using Ollama"""
    prompt = build_rag_prompt(user_question, rag_context)
    return ask_ollama(prompt)

# ── TEST (only run after Ollama is installed) ─────────────────
if __name__ == "__main__":
    print("Testing Ollama connection...")
    test = ask_ollama("Say: OLLAMA WORKING")
    print(f"Response: {test}")

    if "error" not in test.lower():
        print("\nTesting intent parser...")
        tests = [
            "Simulate Mars orbit for 2 years",
            "What is a Hohmann transfer?",
            "Show Jupiter lagrange points",
            "What is the weather today?"
        ]
        for q in tests:
            print(f"\nInput: {q}")
            result = parse_intent(q)
            print(f"Intent: {json.dumps(result, indent=2)}")
    else:
        print("Ollama not ready yet — install it first then run this file")