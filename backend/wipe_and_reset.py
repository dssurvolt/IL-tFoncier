import psycopg
import time

DB_URL = "postgresql://postgres.zdheryarqxqpgxirbqkh:V8oknSECpa1AKPZ0@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

def wipe_and_reset():
    print("🧨 Destruction sécurisée du schéma obsolète...")
    try:
        conn = psycopg.connect(DB_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            # Action radicale : on rase le schéma public et on le recrée
            cur.execute("DROP SCHEMA public CASCADE;")
            cur.execute("CREATE SCHEMA public;")
            cur.execute("GRANT ALL ON SCHEMA public TO postgres;")
            cur.execute("GRANT ALL ON SCHEMA public TO public;")
        conn.close()
        print("✨ Schéma public réinitialisé !")
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage : {e}")

if __name__ == "__main__":
    wipe_and_reset()
