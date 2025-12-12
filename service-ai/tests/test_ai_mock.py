from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_ai_mock_chat_basic_contract():
    payload = {
        "tenant_id": "test-tenant",
        "skill": "test-skill",
        "query": "Domanda di prova dal test",
        "locale": "it-IT",
        "metadata": {"source": "pytest"},
    }

    response = client.post("/v1/ai/mock-chat", json=payload)

    # Deve rispondere 200 OK
    assert response.status_code == 200

    data = response.json()

    # Controllo del contratto base
    assert data["tenant_id"] == payload["tenant_id"]
    assert data["skill"] == payload["skill"]
    assert data["provider"] == "mock"

    # La risposta deve includere almeno la query originale
    assert "Domanda di prova dal test" in data["answer"]

    # Debug strutturato
    assert "debug" in data
    assert isinstance(data["debug"], dict)
    assert "model_name" in data["debug"]
    assert "device" in data["debug"]
    assert "max_tokens" in data["debug"]
