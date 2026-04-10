import os
import psycopg

DB_URL = "postgresql://postgres.zdheryarqxqpgxirbqkh:V8oknSECpa1AKPZ0@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

def check_tables():
    print("📋 Liste des tables dans Supabase :")
    try:
        conn = psycopg.connect(DB_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = cur.fetchall()
            for t in tables:
                print(f"- {t[0]}")
                # Si c'est 'users', on check les colonnes
                if t[0] == 'users':
                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users';")
                    cols = cur.fetchall()
                    print(f"  ↪️ Colonnes : {[c[0] for c in cols]}")
        conn.close()
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    check_tables()
