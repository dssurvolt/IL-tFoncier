# 🏛️ iLÔT FONCIER - ARCHITECTURE TECHNIQUE (V4.0)
## Approche Hybride : Blockchain (Vérité) + Indexer (Vitesse)

> **⚠️ CHANGEMENT MAJEUR (Oct 2025) :** 
> Nous avons abandonné l'architecture centralisée classique pour une architecture décentralisée optimisée.
> Voir le document de référence : [ilot_database_architecture.md](./ilot_database_architecture.md)

---

## 🎯 EN BREF

iLôt Foncier n'est pas une simple application Web. C'est un protocole de validation foncière.
Notre base de données ne stocke pas la "vérité" (qui est sur la Blockchain), mais sert d'index ultra-rapide pour l'expérience utilisateur.

### Les 3 Piliers Techniques :

1.  **Smart Contracts (Polygon/Celo)** : Gèrent la propriété, les transferts et l'escrow. Immuable.
2.  **PostgreSQL + PostGIS (L'Indexer)** : Écoute la blockchain et permet des recherches géospatiales instantanées (ex: "Terrains à 500m").
3.  **IPFS (Stockage)** : Les photos et documents ne sont pas sur nos serveurs, mais sur le réseau décentralisé.

---

## 📂 STRUCTURE DE LA DOCUMENTATION

*   **`ilot_database_architecture.md`** : Le schéma complet des 12 tables optimisées.
*   **`DIAGRAMME_ER_VISUEL.md`** : (Obsolète - En cours de mise à jour pour refléter la V4).

---

## ⚡ PERFORMANCE

*   **USSD Ready** : Table dédiée `ussd_sessions` pour une réponse < 200ms sur téléphones basiques.
*   **Geo-Spatial** : Utilisation native de PostGIS pour valider la présence physique des témoins (Geofencing).
*   **Lightweight** : Base de données 90% plus légère que l'architecture précédente.

---

**Contact Lead Dev :** Pour toute question sur l'implémentation du Sync Node.
