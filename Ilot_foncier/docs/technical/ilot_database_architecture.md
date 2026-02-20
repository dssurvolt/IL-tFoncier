# iLÔT FONCIER - ARCHITECTURE DE BASE DE DONNÉES (V4.1)
## Spécifications Techniques Détaillées - Architecture Hybride (Indexer)

**Version :** 4.1 (Finale)
**Date :** Décembre 2025
**Audience :** Développeurs Backend, Blockchain Engineers, DevOps.

---

## 1. VUE D'ENSEMBLE

Cette base de données PostgreSQL n'est **PAS** la source de vérité pour la propriété (qui est la Blockchain).
Elle agit comme un **Indexeur Haute Performance** (Layer 2 Off-chain) et une couche de gestion pour l'expérience utilisateur (App Mobile & USSD).

### Rôles de la Base de Données :
1.  **Cache Rapide :** Servir les données en < 100ms (impossible via RPC Blockchain direct).
2.  **Recherche Spatiale :** Trouver des terrains par géolocalisation (PostGIS).
3.  **Tampon USSD :** Gérer les sessions interactives pour téléphones basiques.
4.  **Relais Média :** Stocker les références IPFS (CIDs) des documents.

---

## 2. SCHÉMA DÉTAILLÉ (12 TABLES)

### 👤 MODULE A : IDENTITÉ & ACCÈS (3 Tables)

#### 1. `users`
*Table centrale liant l'identité Web3 (Wallet) à l'identité physique (Téléphone).*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Identifiant interne unique. |
| `wallet_address` | VARCHAR(42) | UNIQUE | Adresse publique (0x...). **Clé d'accès principale.** |
| `phone_hash` | VARCHAR(64) | UNIQUE | Hash SHA-256 du numéro de téléphone (Privacy). |
| `encrypted_phone` | VARCHAR | - | Numéro chiffré (pour notifications SMS/USSD). |
| `role` | ENUM | IDX | `USER`, `WITNESS` (Témoin), `CHIEF` (Chef local), `ADMIN`. |
| `reputation_score` | INT | - | Score 0-100 basé sur la qualité des validations passées. |
| `created_at` | TIMESTAMP | - | Date d'inscription. |

#### 2. `auth_nonces`
*Sécurité pour le "Sign-in with Wallet". Empêche les attaques par rejeu.*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `wallet_address` | VARCHAR(42) | PK | Adresse du wallet tentant de se connecter. |
| `nonce` | VARCHAR(32) | - | Chaîne aléatoire à signer par le wallet. |
| `expires_at` | TIMESTAMP | - | Validité courte (ex: 5 minutes). |

#### 3. `ussd_sessions`
*Gestion d'état pour le protocole USSD (qui est stateless par nature).*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `session_id` | VARCHAR(64) | PK | ID de session fourni par l'opérateur télécom. |
| `phone_number` | VARCHAR(20) | IDX | Numéro de l'utilisateur (clair, car session active). |
| `current_menu` | VARCHAR(50) | - | Écran actuel (ex: `HOME`, `REGISTER_GPS`, `CONFIRM`). |
| `input_buffer` | JSONB | - | Données temporaires saisies (ex: `{ "lat": ..., "lng": ... }`). |
| `updated_at` | TIMESTAMP | - | Pour le nettoyage automatique (TTL 3 min). |

---

### 🏘️ MODULE B : PROPRIÉTÉ & BLOCKCHAIN (3 Tables)

#### 4. `properties`
*Miroir local des actifs sur la Blockchain. Mise à jour par l'Indexeur.*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | ID interne. |
| `on_chain_id` | NUMERIC(78) | UNIQUE | ID du Token (NFT/SBT) sur le Smart Contract. `NULL` si brouillon. |
| `owner_wallet` | VARCHAR(42) | IDX | Adresse du propriétaire actuel. |
| `gps_centroid` | GEOGRAPHY(POINT) | GIST | Point central pour recherche rapide "autour de moi". |
| `gps_boundaries` | GEOGRAPHY(POLYGON)| GIST | Limites exactes du terrain. |
| `status` | ENUM | IDX | `DRAFT`, `VALIDATING`, `ON_CHAIN`, `DISPUTED`. |
| `last_sync_block` | BIGINT | - | Dernier bloc blockchain où cet état a été confirmé. |

#### 5. `property_media`
*Liens vers les fichiers stockés sur IPFS. Ne stocke JAMAIS de binaire.*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | - |
| `property_id` | UUID | FK | Lien vers la propriété. |
| `ipfs_cid` | VARCHAR(64) | - | Content ID IPFS (ex: `QmX...`). |
| `media_type` | ENUM | - | `PHOTO_LAND`, `PHOTO_DOC`, `VIDEO_DRONE`. |
| `is_verified` | BOOLEAN | - | `TRUE` si le hash est confirmé sur la blockchain. |

#### 6. `blockchain_sync_status`
*État de santé de l'Indexeur. Critique pour la cohérence des données.*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `contract_address` | VARCHAR(42) | PK | Adresse du Smart Contract surveillé. |
| `chain_id` | INT | - | ID de la chaîne (ex: 137 pour Polygon). |
| `last_processed_block`| BIGINT | - | Dernier bloc lu et indexé avec succès. |
| `sync_status` | ENUM | - | `OK`, `LAGGING`, `STOPPED`. |

---

### 🤝 MODULE C : CONSENSUS & VALIDATION (3 Tables)

#### 7. `validation_requests`
*Processus de validation communautaire avant minting sur la blockchain.*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | - |
| `property_id` | UUID | FK | Propriété en attente de validation. |
| `requester_wallet` | VARCHAR(42) | - | Celui qui demande la validation. |
| `gps_at_request` | GEOGRAPHY(POINT) | - | Preuve de présence physique lors de la demande. |
| `min_witnesses` | INT | - | Nombre minimum de témoins requis (défaut: 3). |
| `status` | ENUM | IDX | `OPEN`, `COMPLETED`, `REJECTED`. |

#### 8. `witness_votes`
*Votes individuels des témoins (Voisins/Chefs).*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | - |
| `request_id` | UUID | FK | Lien vers la demande. |
| `witness_wallet` | VARCHAR(42) | IDX | Qui a voté. |
| `witness_gps` | GEOGRAPHY(POINT) | GIST | **CRITIQUE :** Localisation du témoin au moment du vote. |
| `vote_result` | BOOLEAN | - | `TRUE` (Valide) / `FALSE` (Fraude). |
| `signature` | VARCHAR | - | Signature cryptographique du vote (EIP-712). |

#### 9. `geo_fences`
*Découpage administratif pour assigner les validateurs locaux.*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | - |
| `name` | VARCHAR | - | Nom du quartier/village. |
| `boundary` | GEOGRAPHY(POLYGON)| GIST | Zone géographique. |
| `chief_wallet` | VARCHAR(42) | - | Wallet du chef de quartier (pour arbitrage). |

---

### 💰 MODULE D : MARKETPLACE & ACTIVITÉ (3 Tables)

#### 10. `listings`
*Offres de vente (Layer 2).*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | - |
| `property_id` | UUID | FK | Propriété à vendre. |
| `price_fiat` | DECIMAL | - | Prix affiché (FCFA/USD). |
| `price_crypto` | DECIMAL | - | Équivalent stablecoin (cUSD/USDT). |
| `escrow_contract` | VARCHAR(42) | - | Adresse du contrat séquestre déployé. |
| `status` | ENUM | IDX | `ACTIVE`, `SOLD`, `CANCELLED`. |

#### 11. `transactions_history`
*Journal d'activité enrichi (Off-chain + On-chain).*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | - |
| `tx_hash` | VARCHAR(66) | UNIQUE | Hash de la transaction blockchain. |
| `event_type` | VARCHAR | IDX | `MINT`, `TRANSFER`, `VALIDATE`, `DISPUTE`. |
| `from_address` | VARCHAR(42) | - | Initiateur. |
| `to_address` | VARCHAR(42) | - | Destinataire (si applicable). |
| `metadata` | JSONB | - | Détails contextuels (prix, commentaires). |

#### 12. `notifications`
*Système d'alerte utilisateur.*

| Colonne | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | - |
| `user_wallet` | VARCHAR(42) | IDX | Destinataire. |
| `type` | VARCHAR | - | `VALIDATION_NEEDED`, `OFFER_RECEIVED`, `TX_CONFIRMED`. |
| `payload` | JSONB | - | Données pour l'UI. |
| `read_at` | TIMESTAMP | - | État de lecture. |

---

## 3. NOTES D'IMPLÉMENTATION

### Stack Recommandée
*   **DB Engine :** PostgreSQL 15+
*   **Extensions :** `postgis` (Géospatial), `pgcrypto` (UUID).
*   **ORM :** Prisma ou TypeORM (Node.js).

### Indexation Spatiale (GIST)
Toutes les colonnes `GEOGRAPHY` utilisent des index GIST.
Exemple de requête performante :
```sql
-- Trouver les propriétés dans un rayon de 500m
SELECT * FROM properties 
WHERE ST_DWithin(gps_centroid, ST_MakePoint(long, lat)::geography, 500);
```

### Sécurité
*   Aucun mot de passe utilisateur n'est stocké (Auth via Wallet).
*   Les numéros de téléphone sont hashés pour la confidentialité, sauf dans `ussd_sessions` (éphémère) et `encrypted_phone` (nécessite clé privée serveur).
