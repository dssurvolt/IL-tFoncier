# DIAGRAMME ER - ARCHITECTURE HYBRIDE (V4.1)
## Blockchain (Polygon) + Indexer (PostgreSQL)

Ce diagramme reflète l'architecture optimisée à **12 tables**, centrée sur la synchronisation Blockchain et la validation communautaire.

```mermaid
erDiagram
    %% MODULE A: IDENTITÉ & ACCÈS
    USERS ||--o{ PROPERTIES : owns_wallet
    USERS ||--o{ WITNESS_VOTES : signs_vote
    USERS ||--o{ VALIDATION_REQUESTS : initiates
    USERS ||--o{ NOTIFICATIONS : receives
    USERS {
        uuid id PK
        varchar wallet_address UK "Clé Publique (Identity)"
        varchar phone_hash "Privacy Hash"
        varchar encrypted_phone
        int reputation_score
        enum role "USER, WITNESS, CHIEF"
    }

    AUTH_NONCES {
        varchar wallet_address PK
        varchar nonce "Anti-Replay"
        timestamp expires_at
    }

    USSD_SESSIONS {
        varchar session_id PK
        varchar phone_number
        jsonb input_buffer "Stateless storage"
        timestamp updated_at "TTL 3min"
    }

    %% MODULE B: PROPRIÉTÉ & BLOCKCHAIN
    PROPERTIES ||--o{ PROPERTY_MEDIA : contains
    PROPERTIES ||--o{ LISTINGS : listed_in
    PROPERTIES ||--o{ VALIDATION_REQUESTS : subject_of
    PROPERTIES {
        uuid id PK
        uint256 on_chain_id UK "Token ID (Smart Contract)"
        varchar owner_wallet FK
        geography gps_centroid "GIST Index"
        geography gps_boundaries "GIST Index"
        enum status "DRAFT, ON_CHAIN"
        int last_sync_block
    }

    PROPERTY_MEDIA {
        uuid id PK
        uuid property_id FK
        varchar ipfs_cid "IPFS Hash"
        enum media_type "PHOTO, DOC"
        bool is_verified
    }

    BLOCKCHAIN_SYNC_STATUS {
        varchar contract_address PK
        int last_processed_block
        enum sync_status
    }

    %% MODULE C: CONSENSUS & VALIDATION
    VALIDATION_REQUESTS ||--o{ WITNESS_VOTES : collects
    VALIDATION_REQUESTS {
        uuid id PK
        uuid property_id FK
        varchar requester_wallet
        geography gps_at_request "Proof of Presence"
        enum status "OPEN, COMPLETED"
    }

    WITNESS_VOTES {
        uuid id PK
        uuid request_id FK
        varchar witness_wallet FK
        geography witness_gps "Proof of Presence"
        bool vote_result
        varchar signature "EIP-712"
    }

    GEO_FENCES {
        uuid id PK
        varchar name "Quartier/Village"
        geography boundary "Zone Admin"
        varchar chief_wallet
    }

    %% MODULE D: MARKETPLACE & ACTIVITÉ
    LISTINGS {
        uuid id PK
        uuid property_id FK
        decimal price_fiat
        decimal price_crypto
        varchar escrow_contract
        enum status
    }

    TRANSACTIONS_HISTORY {
        uuid id PK
        varchar tx_hash UK "On-chain TX"
        varchar event_type
        jsonb metadata
    }

    NOTIFICATIONS {
        uuid id PK
        varchar user_wallet FK
        varchar type
        jsonb payload
        timestamp read_at
    }
```

### Légende Technique
*   **12 Tables Essentielles** : Couvrent l'intégralité du flux Hybride (Off-chain <-> On-chain).
*   **GIST Index** : Indique les colonnes optimisées pour la recherche spatiale (PostGIS).
*   **UK** : Unique Key.
*   **FK** : Foreign Key.
