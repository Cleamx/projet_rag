#!/usr/bin/env python3
"""
Script de test pour le système RAG GLPI
Teste les différents endpoints et affiche les résultats
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """Affiche un titre de section"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_glpi_stats():
    """Teste l'endpoint des statistiques GLPI"""
    print_section("📊 Test: Statistiques GLPI")
    try:
        response = requests.get(f"{BASE_URL}/glpi/stats")
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_glpi_preview(source_type: str):
    """Teste l'endpoint de prévisualisation GLPI"""
    print_section(f"👀 Test: Aperçu {source_type}")
    try:
        response = requests.get(f"{BASE_URL}/glpi/preview/{source_type}")
        response.raise_for_status()
        data = response.json()
        
        # Afficher seulement les 2 premiers pour ne pas surcharger
        if "data" in data:
            items = data["data"][:2]
            for item in items:
                print(f"ID: {item.get('id', 'N/A')}")
                print(f"Title: {item.get('title', item.get('question', 'N/A'))}")
                print(f"Category: {item.get('category', 'N/A')}")
                print("-" * 40)
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_ask_question(question: str, user_id: int = 1):
    """Teste une question avec le système RAG"""
    print_section(f"💬 Test Question: '{question}'")
    try:
        payload = {
            "user_ad_id": user_id,
            "question": question
        }
        response = requests.post(f"{BASE_URL}/ask/", json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"Question: {data.get('question', 'N/A')}")
        print(f"\n✅ Réponse:\n{data.get('answer', 'N/A')}")
        
        if "sources" in data and data["sources"]:
            print(f"\n📚 Sources utilisées ({len(data['sources'])}):")
            for i, source in enumerate(data["sources"], 1):
                print(f"\n  [{i}] {source.get('type', 'N/A')} #{source.get('id', 'N/A')}")
                print(f"      {source.get('title', 'N/A')}")
                if 'metadata' in source:
                    meta = source['metadata']
                    if 'category' in meta:
                        print(f"      Catégorie: {meta['category']}")
        else:
            print("\n⚠️  Aucune source GLPI trouvée")
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("\n" + "="*60)
    print("  🧪 TEST DU SYSTÈME RAG GLPI")
    print("="*60)
    
    results = []
    
    # Test 1: Statistiques GLPI
    results.append(("Stats GLPI", test_glpi_stats()))
    
    # Test 2: Aperçu des sources
    results.append(("Preview Tickets", test_glpi_preview("tickets")))
    results.append(("Preview KB Articles", test_glpi_preview("kb_articles")))
    results.append(("Preview FAQ", test_glpi_preview("faq")))
    
    # Test 3: Questions RAG
    test_questions = [
        "Comment me connecter au VPN ?",
        "Mon imprimante ne fonctionne pas",
        "J'ai oublié mon mot de passe",
        "Outlook est très lent, que faire ?",
    ]
    
    for q in test_questions:
        results.append((f"Question: {q[:30]}...", test_ask_question(q)))
    
    # Résumé
    print_section("📋 Résumé des tests")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés !")
    else:
        print(f"\n⚠️  {total - passed} test(s) ont échoué")

if __name__ == "__main__":
    main()
