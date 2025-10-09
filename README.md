# Test de la branche `test_api_mistral`

But: objectif court pour tester l'intégration / comportement de l'API Mistral sur la branche `test_api_mistral`.

## Installation rapide
1. Basculer sur la branche de test
     ```bash
     git fetch
     git checkout test_api_mistral
     ```
2. Installer les dépendances (adapter selon le projet)
     - Python:
         ```bash
         pip install -r requirements.txt
         ```

## Configuration
Créer un fichier `.env` ou exporter les variables d'environnement:
```bash
MISTRAL_API_KEY = votre_cle
# or
export MISTRAL_API_KEY="votre_cle"
```

## Exécution / Tests
- Lancer l'application (adapter la commande):
    - Python:
        ```bash
        python test_api_mistral.py
        ```


## Comportement attendu
- Les endpoints/appels utilisant l'API Mistral doivent répondre sans erreurs avec la clé fournie.
- Les tests automatiques liés à Mistral doivent passer (ou indiquer clairement les points d'échec).

## Dépannage rapide
- Vérifier que `MISTRAL_API_KEY` est valide.
- Activer les logs (si disponible) pour tracer les requêtes.
- S'assurer que la branche locale est à jour: `git pull --rebase origin test_api_mistral`
