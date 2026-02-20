# 📘 iLôt Foncier - Documentation Technique Backend (Master)

> **Dernière mise à jour :** 28 Décembre 2025
> **Version :** 1.0.0
> **Responsable :** Équipe Backend

Ce document est la **source unique de vérité** pour l'architecture technique, les APIs, et les flux métier du backend iLôt Foncier.

---

## 1. Architecture Globale

Le backend est construit sur **Django** (Python) et suit une architecture modulaire alignée sur la vision Web3 (Indexeur Off-chain + Blockchain).

### Modules (Django Apps)
1.  **Identity (`identity`)** : Gestion des utilisateurs (Wallets), Authentification, et **Passerelle USSD**.
2.  **Land Registry (`land_registry`)** : Cœur du système. Gestion des propriétés (`Property`), géolocalisation, et synchronisation Blockchain.
3.  **Consensus (`consensus`)** : Logique de validation communautaire (`ValidationRequest`, `WitnessVote`).
4.  **Marketplace (`marketplace`)** : Gestion des offres de vente (`Listing`) et transactions.

---

## 2. Base de Données (12 Tables)

L'architecture est hybride. La base de données sert d'indexeur performant pour les données qui seront ancrées sur la Blockchain.

### Schéma Simplifié
*   **Users** : `wallet_address` (PK), `reputation_score`, `role`.
*   **Properties** : `gps_centroid`, `gps_boundaries`, `status` (DRAFT -> VALIDATING -> ON_CHAIN).
*   **ValidationRequests** : Lien entre une propriété et les votes des témoins.
*   **USSDSessions** : Gestion de l'état des menus pour les téléphones basiques.

---

## 3. API Reference (REST)

La documentation interactive est disponible sur `/swagger/`.

### Endpoints Principaux
*   **Propriétés** :
    *   `GET /api/properties/` : Lister les terrains.
    *   `POST /api/properties/` : Créer un brouillon.
*   **Consensus** :
    *   `POST /api/validation/request/` : Demander une validation.
    *   `POST /api/validation/vote/` : Voter (Voisin).
*   **Marketplace** :
    *   `GET /api/marketplace/listings/` : Voir les offres.
*   **Identity** :
    *   `GET /api/identity/profile/{wallet}/` : Profil public.

---

## 4. Système USSD (Menu *123#)

Le système USSD permet l'inclusion numérique des utilisateurs sans smartphone.

### Arborescence des Menus (V2 - Validée)

1.  **Accueil**
    *   1. 🏗️ Enregistrer un terrain (Déclaration)
    *   2. 🤝 Valider un terrain (Témoin)
    *   3. 👤 Mon Compte (Réputation & Solde)
    *   4. ℹ️ Aide

2.  **Détails des Flux**
    *   **Enregistrement** : L'utilisateur déclare successivement la latitude, la longitude et la superficie. Un `Property` en état `DRAFT` est créé avec ces coordonnées précises. L'ID court (8 premiers caractères de l'UUID) est retourné.
    *   **Validation** : Le témoin entre l'ID du terrain. Le système vérifie l'existence, crée une `ValidationRequest` si nécessaire, et enregistre un `WitnessVote`.
    *   **Mon Compte** : Affiche le rôle, le score de réputation et le nombre de terrains possédés.

### Audit de Qualité & Tests Automatisés
Un audit complet a été réalisé le 28/12/2025. Le script `test_all_flows.py` permet de vérifier l'intégralité des flux métier en une commande.

**Points vérifiés :**
*   **Consensus** : 3 votes positifs = Passage automatique en `ON_CHAIN`.
*   **Sécurité Marketplace** : Vérification stricte de la propriété (Owner) et du statut du terrain.
*   **Robustesse USSD** : Gestion des sessions et des contraintes de base de données.

---

## 5. Commandes Utiles

*   **Lancer le serveur** : `python manage.py runserver`
*   **Audit de Qualité (Complet)** : `python3 test_all_flows.py`
*   **Tests Unitaires** : `python manage.py test`
*   **Swagger** : `http://localhost:8000/swagger/`
