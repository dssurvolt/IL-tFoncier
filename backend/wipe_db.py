import psycopg

DB_URL = "postgresql://postgres.zdheryarqxqpgxirbqkh:V8oknSECpa1AKPZ0@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

def wipe_db():
    print("🧨 Vidage complet de la base Supabase (Public Schema)...")
    try:
        conn = psycopg.connect(DB_URL)
        with conn.cursor() as cur:
            # Récupère toutes les tables du schéma public
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = cur.fetchall()
            for t in tables:
                print(f"🗑️ Suppression de {t[0]}...")
                cur.execute(f"DROP TABLE IF EXISTS \"{t[0]}\" CASCADE;")
            conn.commit()
        conn.close()
        print("✨ Base nettoyée !")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    wipe_db()
