import psycopg

DB_URL = "postgresql://postgres.zdheryarqxqpgxirbqkh:V8oknSECpa1AKPZ0@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

def check_all_columns():
    try:
        conn = psycopg.connect(DB_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = [t[0] for t in cur.fetchall()]
            for table in tables:
                print(f"\n📊 TABLE: {table}")
                cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';")
                cols = cur.fetchall()
                for c in cols:
                    print(f"  - {c[0]} ({c[1]})")
        conn.close()
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    check_all_columns()
