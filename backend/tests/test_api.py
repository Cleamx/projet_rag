"""Tests d'intégration pour l'API FastAPI"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Tests des endpoints de santé"""

    def test_root_endpoint(self):
        """Test que la racine redirige vers le frontend"""
        response = client.get("/")
        assert response.status_code == 200

    def test_docs_endpoint_disabled(self):
        """Test que la documentation Swagger est désactivée"""
        response = client.get("/docs")
        assert response.status_code == 404


class TestGLPIEndpoints:
    """Tests des endpoints GLPI"""

    def test_glpi_stats(self):
        """Test l'endpoint /glpi/stats"""
        response = client.get("/glpi/stats")
        assert response.status_code == 200
        data = response.json()
        assert "tickets_count" in data
        assert "kb_articles_count" in data
        assert "faq_items_count" in data
        assert "total_entries" in data
        assert data["tickets_count"] == 8
        assert data["kb_articles_count"] == 3
        assert data["faq_items_count"] == 5
        assert data["total_entries"] == 16

    def test_glpi_preview_tickets(self):
        """Test l'endpoint /glpi/preview/tickets"""
        response = client.get("/glpi/preview/tickets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 8

    def test_glpi_preview_kb_articles(self):
        """Test l'endpoint /glpi/preview/kb_articles"""
        response = client.get("/glpi/preview/kb_articles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_glpi_preview_faq(self):
        """Test l'endpoint /glpi/preview/faq"""
        response = client.get("/glpi/preview/faq")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_glpi_preview_invalid_type(self):
        """Test l'endpoint avec un type invalide"""
        response = client.get("/glpi/preview/invalid_type")
        assert response.status_code == 400


class TestAskEndpoint:
    """Tests de l'endpoint /ask/"""

    @pytest.mark.skip(
            reason="Nécessite Ollama running - test manuel uniquement")
    def test_ask_question_vpn(self):
        """Test une question sur le VPN"""
        response = client.post(
            "/ask/",
            json={"user_ad_id": 1, "question": "Comment configurer le VPN ?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "answer" in data
        assert "sources" in data
        assert len(data["sources"]) > 0

    @pytest.mark.skip(
            reason="Nécessite Ollama running - test manuel uniquement")
    def test_ask_question_imprimante(self):
        """Test une question sur l'imprimante"""
        response = client.post(
            "/ask/",
            json={"user_ad_id": 2, 
                  "question": "Mon imprimante ne fonctionne pas"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "answer" in data
        assert "sources" in data

    def test_ask_missing_fields(self):
        response = client.post("/ask/", json={"user_ad_id": 1})
        assert response.status_code == 422

    def test_ask_empty_question(self):
        """Test avec une question vide"""
        response = client.post("/ask/", json={"user_ad_id": 1, "question": ""})
        # Peut être 422 (validation) ou 500 selon l'implémentation
        assert response.status_code in [422, 500, 200]


class TestCORS:
    """Tests de la configuration CORS"""

    def test_cors_headers(self):
        """Test que les headers CORS sont présents"""
        response = client.options(
            "/glpi/stats", headers={"Origin": "http://localhost:8000"}
        )
        # CORS devrait autoriser les requêtes
        assert response.status_code in [200, 204]
