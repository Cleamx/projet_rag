"""Tests unitaires pour les modèles SQLModel."""
import pytest
from app.models import Technicien, Reponse, Question


class TestTechnicienModel:
    """Tests du modèle Technicien."""

    def test_technicien_creation(self):
        """Test création d'un technicien."""
        tech = Technicien(
            nom="Test Tech",
            email="test@example.com",
            description="Description test"
        )
        assert tech.nom == "Test Tech"
        assert tech.email == "test@example.com"
        assert tech.description == "Description test"
        assert tech.id is None  # Not persisted yet

    def test_technicien_without_description(self):
        """Test création d'un technicien sans description."""
        tech = Technicien(nom="Tech", email="tech@example.com")
        assert tech.nom == "Tech"
        assert tech.description is None


class TestQuestionModel:
    """Tests du modèle Question."""

    def test_question_creation(self):
        """Test création d'une question."""
        question = Question(
            user_ad_id=1,
            question_label="Comment configurer le VPN ?",
            embedding_question="[0.1, 0.2, 0.3]"
        )
        assert question.user_ad_id == 1
        assert question.question_label == "Comment configurer le VPN ?"
        assert question.id is None

    def test_question_with_different_user(self):
        """Test question avec différents utilisateurs."""
        q1 = Question(user_ad_id=1, question_label="Q1", embedding_question="[]")
        q2 = Question(user_ad_id=2, question_label="Q2", embedding_question="[]")
        assert q1.user_ad_id != q2.user_ad_id


class TestReponseModel:
    """Tests du modèle Reponse."""

    def test_reponse_creation(self):
        """Test création d'une réponse."""
        reponse = Reponse(
            reponse_label="Voici comment configurer le VPN...",
            question_id=1
        )
        assert reponse.reponse_label == "Voici comment configurer le VPN..."
        assert reponse.question_id == 1
        assert reponse.validite == 0  # Default
        assert reponse.nombre_resolution == 0  # Default
        assert reponse.technicien_id is None  # Optional

    def test_reponse_with_technicien(self):
        """Test réponse avec technicien assigné."""
        reponse = Reponse(
            reponse_label="Réponse",
            question_id=1,
            technicien_id=5
        )
        assert reponse.technicien_id == 5

    def test_reponse_validite_values(self):
        """Test les valeurs de validité."""
        # Valide
        r_valid = Reponse(reponse_label="R", question_id=1, validite=1)
        assert r_valid.validite == 1
        
        # Invalide
        r_invalid = Reponse(reponse_label="R", question_id=1, validite=-1)
        assert r_invalid.validite == -1
        
        # Neutre (default)
        r_neutral = Reponse(reponse_label="R", question_id=1)
        assert r_neutral.validite == 0
