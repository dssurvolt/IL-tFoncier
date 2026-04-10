import os
import psycopg
from dotenv import load_dotenv

# Charge l'URL Supabase (Version Pooler pour éviter IPv6)
DB_URL = "postgresql://postgres.zdheryarqxqpgxirbqkh:V8oknSECpa1AKPZ0@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

def fix_db_schema():
    print("🚀 Tentative de réparation chirurgicale du schéma Supabase...")
    try:
        conn = psycopg.connect(DB_URL)
        with conn.cursor() as cur:
            # 1. Vérifier si 'phone' existe
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='phone';")
            if not cur.fetchone():
                print("➕ Ajout de la colonne 'phone' à la table 'users'...")
                cur.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20) UNIQUE;")
                conn.commit()
                print("✅ Colonne 'phone' ajoutée !")
            else:
                print("ℹ️ La colonne 'phone' existe déjà.")

            # 2. Vérifier 'full_name'
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='full_name';")
            if not cur.fetchone():
                print("➕ Ajout de la colonne 'full_name'...")
                cur.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR(255);")
                conn.commit()
            
            # Vous pouvez ajouter d'autres colonnes ici si nécessaire
            
        conn.close()
        print("🎉 Réparation terminée avec succès !")
    except Exception as e:
        print(f"❌ Erreur lors de la réparation : {e}")

if __name__ == "__main__":
    fix_db_schema()
