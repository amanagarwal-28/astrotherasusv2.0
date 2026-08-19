"""
Validates that core orbital-dynamics queries resolve to a correct scenario
through pattern-matching alone (source == "builtin"), without needing an
LLM. These are the phrases a student/enthusiast would actually type, so a
regression here silently degrades to (or fails without) Ollama.
"""
import pytest

from ai_scenario_generator import get_scenario


@pytest.mark.parametrize("prompt,expected_name_substr", [
    ("hohmann transfer earth to mars", "Earth"),
    ("transfer from venus to jupiter", "Venus"),
    ("lagrange point", "Trojan"),
    ("jupiter trojan asteroid L5", "L5"),
    ("orbital resonance 3:2", "3:2"),
    ("binary star system", "Binary"),
    ("eccentric binary star", "Binary"),
    ("solar system", "Solar System"),
    ("mars orbit", "Mars"),
    ("earth moon", "Earth-Moon"),
])
def test_orbital_dynamics_prompts_resolve_without_llm(prompt, expected_name_substr):
    result = get_scenario(prompt)
    assert result["ok"] is True
    assert result["source"] == "builtin"
    assert expected_name_substr.lower() in result["scenario"]["name"].lower()


def test_hohmann_transfer_respects_mentioned_order():
    # "venus to jupiter" must depart from Venus, not swap to alphabetical
    # or dict-iteration order.
    result = get_scenario("hohmann transfer venus to jupiter")
    assert result["scenario"]["name"] == "Hohmann: Venus → Jupiter"


def test_hohmann_transfer_defaults_to_earth_mars_when_no_body_named():
    result = get_scenario("show me a hohmann transfer")
    assert result["scenario"]["name"] == "Hohmann: Earth → Mars"


def test_lagrange_defaults_to_l4_jupiter():
    result = get_scenario("show a trojan asteroid")
    assert result["scenario"]["name"] == "Jupiter L4 Trojan Point"
