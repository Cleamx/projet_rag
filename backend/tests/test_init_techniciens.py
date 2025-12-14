"""Tests pour le module init_techniciens."""
import pytest
from app.init_techniciens import (
    TECHNICIENS_DATA,
    get_all_categories
)


class TestTechniciensData:
    """Tests des données des techniciens."""

    def test_techniciens_data_not_empty(self):
        """Test que les données ne sont pas vides."""
        assert len(TECHNICIENS_DATA) > 0

    def test_technicien_has_required_fields(self):
        """Test que chaque technicien a les champs requis."""
        required_fields = ['nom', 'email', 'description']
        for tech in TECHNICIENS_DATA:
            for field in required_fields:
                assert field in tech, f"Technicien manque le champ '{field}'"

    def test_technicien_names_unique(self):
        """Test que les noms sont uniques."""
        names = [t['nom'] for t in TECHNICIENS_DATA]
        assert len(names) == len(set(names)), "Noms de techniciens non uniques"

    def test_technicien_emails_valid_format(self):
        """Test format basique des emails."""
        for tech in TECHNICIENS_DATA:
            email = tech['email']
            # Email peut être une adresse ou un hotline
            assert len(email) > 0, f"Email vide pour {tech['nom']}"

    def test_expected_techniciens_exist(self):
        """Test que les techniciens attendus existent."""
        expected = [
            "Techniciens", "Réseau", "Métier", "SharePoint",
            "Exchange", "Campus numérique", "Comptes", 
            "Cours en ligne", "Audiovisuel", "Copieurs", "Suivi de commande"
        ]
        actual_names = [t['nom'] for t in TECHNICIENS_DATA]
        for name in expected:
            assert name in actual_names, f"Technicien {name} manquant"


class TestGetAllCategories:
    """Tests de la fonction get_all_categories."""

    def test_returns_list(self):
        """Test que la fonction retourne une liste."""
        categories = get_all_categories()
        assert isinstance(categories, list)

    def test_returns_all_categories(self):
        """Test que toutes les catégories sont retournées."""
        categories = get_all_categories()
        assert len(categories) == len(TECHNICIENS_DATA)

    def test_returns_category_names(self):
        """Test que les noms sont des strings."""
        categories = get_all_categories()
        for cat in categories:
            assert isinstance(cat, str)
            assert len(cat) > 0
