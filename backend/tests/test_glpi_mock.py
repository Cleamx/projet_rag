"""Tests pour le module glpi_mock."""
import pytest
from app.glpi_mock import glpi_mock, GLPIMockData


class TestGLPIMockData:
    """Tests de la classe GLPIMockData."""

    def test_glpi_mock_instance_exists(self):
        """Test que l'instance glpi_mock existe."""
        assert glpi_mock is not None
        assert isinstance(glpi_mock, GLPIMockData)

    def test_tickets_generated(self):
        """Test que les tickets sont générés."""
        assert hasattr(glpi_mock, 'tickets')
        assert isinstance(glpi_mock.tickets, list)
        assert len(glpi_mock.tickets) > 0

    def test_kb_articles_generated(self):
        """Test que les articles KB sont générés."""
        assert hasattr(glpi_mock, 'kb_articles')
        assert isinstance(glpi_mock.kb_articles, list)
        assert len(glpi_mock.kb_articles) > 0

    def test_faq_items_generated(self):
        """Test que les items FAQ sont générés."""
        assert hasattr(glpi_mock, 'faq_items')
        assert isinstance(glpi_mock.faq_items, list)
        assert len(glpi_mock.faq_items) > 0


class TestTicketStructure:
    """Tests de la structure des tickets."""

    def test_ticket_has_required_fields(self):
        """Test que chaque ticket a les champs requis."""
        required_fields = ['id', 'title', 'description', 'category', 'status']
        for ticket in glpi_mock.tickets:
            for field in required_fields:
                assert field in ticket, f"Ticket manque le champ '{field}'"

    def test_ticket_id_is_unique(self):
        """Test que les IDs des tickets sont uniques."""
        ids = [t['id'] for t in glpi_mock.tickets]
        assert len(ids) == len(set(ids)), "IDs des tickets non uniques"


class TestKBArticleStructure:
    """Tests de la structure des articles KB."""

    def test_kb_article_has_required_fields(self):
        """Test que chaque article KB a les champs requis."""
        required_fields = ['id', 'title', 'content', 'category']
        for article in glpi_mock.kb_articles:
            for field in required_fields:
                assert field in article, f"Article KB manque le champ '{field}'"


class TestFAQStructure:
    """Tests de la structure des items FAQ."""

    def test_faq_has_required_fields(self):
        """Test que chaque item FAQ a les champs requis."""
        required_fields = ['id', 'question', 'answer', 'category']
        for faq in glpi_mock.faq_items:
            for field in required_fields:
                assert field in faq, f"FAQ manque le champ '{field}'"


class TestSearchAll:
    """Tests de la fonction search_all."""

    def test_search_returns_list(self):
        """Test que search_all retourne une liste."""
        results = glpi_mock.search_all("VPN")
        assert isinstance(results, list)

    def test_search_with_limit(self):
        """Test la limite de résultats."""
        results = glpi_mock.search_all("problème", limit=2)
        assert len(results) <= 2

    def test_search_empty_query(self):
        """Test recherche avec requête vide."""
        results = glpi_mock.search_all("")
        assert isinstance(results, list)

    def test_search_result_structure(self):
        """Test la structure des résultats de recherche."""
        results = glpi_mock.search_all("VPN", limit=1)
        if results:
            result = results[0]
            expected_fields = ['source', 'id', 'title', 'content', 'metadata']
            for field in expected_fields:
                assert field in result, f"Résultat manque le champ '{field}'"

    def test_search_vpn_returns_results(self):
        """Test recherche VPN retourne des résultats."""
        results = glpi_mock.search_all("VPN")
        assert len(results) > 0, "La recherche VPN devrait retourner des résultats"

    def test_search_imprimante_returns_results(self):
        """Test recherche imprimante retourne des résultats."""
        results = glpi_mock.search_all("imprimante")
        assert len(results) > 0, "La recherche imprimante devrait retourner des résultats"

    def test_search_nonexistent_term(self):
        """Test recherche avec terme inexistant."""
        results = glpi_mock.search_all("xyzabc123nonexistent")
        # Peut retourner des résultats avec score faible ou liste vide
        assert isinstance(results, list)
