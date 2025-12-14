"""Tests pour les fonctions de parsing du module LLM (sans Ollama)."""
import pytest
from app.llm import (
    parse_category_from_response,
    _build_categories_prompt,
    TECHNICIEN_CATEGORIES
)


class TestParseCategoryFromResponse:
    """Tests de la fonction parse_category_from_response."""

    def test_parse_category_with_category_tag(self):
        """Test parsing avec tag [CATEGORY:xxx]."""
        response = "Voici la réponse. [CATEGORY:Réseau]"
        cleaned, category = parse_category_from_response(response)
        assert category == "Réseau"
        assert "[CATEGORY" not in cleaned
        assert "Voici la réponse." in cleaned

    def test_parse_category_with_simple_tag(self):
        """Test parsing avec tag simple [xxx]."""
        response = "Voici la réponse. [Exchange]"
        cleaned, category = parse_category_from_response(response)
        assert category == "Exchange"
        assert "[Exchange]" not in cleaned

    def test_parse_category_case_insensitive(self):
        """Test parsing insensible à la casse."""
        response = "Réponse [CATEGORY:réseau]"
        cleaned, category = parse_category_from_response(response)
        assert category == "Réseau"

    def test_parse_no_category(self):
        """Test parsing sans tag de catégorie."""
        response = "Voici une réponse simple sans catégorie."
        cleaned, category = parse_category_from_response(response)
        assert category is None
        assert cleaned == response.strip()

    def test_parse_invalid_category(self):
        """Test parsing avec catégorie inconnue."""
        response = "Réponse [CATEGORY:CatégorieInexistante]"
        cleaned, category = parse_category_from_response(response)
        assert category is None

    def test_parse_all_known_categories(self):
        """Test parsing de toutes les catégories connues."""
        for cat_name in TECHNICIEN_CATEGORIES.keys():
            response = f"Réponse test [CATEGORY:{cat_name}]"
            cleaned, category = parse_category_from_response(response)
            assert category == cat_name, f"Catégorie {cat_name} non reconnue"

    def test_parse_empty_response(self):
        """Test parsing avec réponse vide."""
        response = ""
        cleaned, category = parse_category_from_response(response)
        assert cleaned == ""
        assert category is None

    def test_parse_whitespace_handling(self):
        """Test gestion des espaces."""
        response = "  Réponse avec espaces  [CATEGORY: Exchange ]  "
        cleaned, category = parse_category_from_response(response)
        assert category == "Exchange"
        assert cleaned.strip() == "Réponse avec espaces"


class TestBuildCategoriesPrompt:
    """Tests de la fonction _build_categories_prompt."""

    def test_prompt_contains_header(self):
        """Test que le prompt contient l'en-tête."""
        prompt = _build_categories_prompt()
        assert "CATÉGORIES DE TECHNICIENS DISPONIBLES" in prompt

    def test_prompt_contains_all_categories(self):
        """Test que le prompt contient toutes les catégories."""
        prompt = _build_categories_prompt()
        for cat_name in TECHNICIEN_CATEGORIES.keys():
            assert cat_name in prompt, f"Catégorie {cat_name} manquante dans le prompt"

    def test_prompt_contains_descriptions(self):
        """Test que le prompt contient les descriptions."""
        prompt = _build_categories_prompt()
        for description in TECHNICIEN_CATEGORIES.values():
            assert description in prompt


class TestTechnicienCategories:
    """Tests des catégories de techniciens."""

    def test_categories_not_empty(self):
        """Test que les catégories ne sont pas vides."""
        assert len(TECHNICIEN_CATEGORIES) > 0

    def test_categories_have_descriptions(self):
        """Test que toutes les catégories ont des descriptions."""
        for name, description in TECHNICIEN_CATEGORIES.items():
            assert isinstance(name, str) and len(name) > 0
            assert isinstance(description, str) and len(description) > 0

    def test_expected_categories_exist(self):
        """Test que les catégories attendues existent."""
        expected = [
            "Techniciens", "Réseau", "Métier", "SharePoint", 
            "Exchange", "Comptes", "Audiovisuel", "Copieurs"
        ]
        for cat in expected:
            assert cat in TECHNICIEN_CATEGORIES, f"Catégorie {cat} manquante"
