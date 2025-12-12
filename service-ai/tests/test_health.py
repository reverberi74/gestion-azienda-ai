from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_ai_mock_chat_basic():
    payload = {
        "tenant_id": "test-tenant",
        "skill": "test-skill",
        "query": "Domanda di prova",
        "locale": "it-IT",
        "metadata": {"source": "pytest"},
    }

    response = client.post("/v1/ai/mock-chat", json=payload)

    assert response.status_code == 200

    data = response.json()

    # Contratto base
    assert data["tenant_id"] == payload["tenant_id"]
    assert data["skill"] == payload["skill"]
    assert data["provider"] == "mock"

    # La risposta deve contenere almeno la query originale
    assert "Domanda di prova" in data["answer"]

    # Debug presente e strutturato
    assert "debug" in data
    assert "model_name" in data["debug"]
    assert "device" in data["debug"]
    assert "max_tokens" in data["debug"]
