import psycopg

# URL Pooler (Indispensable pour contourner IPv6)
DB_URL = "postgresql://postgres.zdheryarqxqpgxirbqkh:V8oknSECpa1AKPZ0@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

def force_schema():
    print("🔥 Forçage de la création de la table app_users...")
    sql = """
    CREATE TABLE IF NOT EXISTS app_users (
        password varchar(128) NOT NULL,
        last_login timestamptz NULL,
        is_superuser boolean NOT NULL,
        id uuid NOT NULL PRIMARY KEY,
        email varchar(254) NOT NULL UNIQUE,
        phone varchar(20) NULL UNIQUE,
        role varchar(20) NOT NULL,
        full_name varchar(255) NULL,
        birth_date date NULL,
        country varchar(100) NOT NULL,
        departement varchar(100) NULL,
        commune varchar(100) NULL,
        district varchar(100) NULL,
        village varchar(100) NULL,
        is_verified boolean NOT NULL,
        created_at timestamptz NOT NULL,
        is_staff boolean NOT NULL,
        is_active boolean NOT NULL,
        date_joined timestamptz NOT NULL,
        first_name varchar(150) NOT NULL,
        last_name varchar(150) NOT NULL
    );
    """
    try:
        conn = psycopg.connect(DB_URL)
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            print("✅ Table app_users créée avec succès !")
    except Exception as e:
        print(f"❌ Échec : {e}")

if __name__ == "__main__":
    force_schema()
