import os
from supabase import create_client, Client
from django.conf import settings

class SupabaseStorageManager:
    """
    Gère le stockage des fichiers sur les Buckets Supabase.
    """
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY # On utilise la clé service ou anon selon config
        self.supabase: Client = create_client(self.url, self.key)
        self.bucket_name = "ilot-media"

    def upload_file(self, file_obj, destination_path):
        """
        Téléverse un objet fichier vers le bucket spécifié.
        """
        try:
            # S'assurer que le fichier est au début
            file_obj.seek(0)
            file_content = file_obj.read()
            
            # TODO: S'assurer que le bucket existe ou a été créé manuellement
            # Détection du type MIME basique selon l'extension
            import mimetypes
            content_type, _ = mimetypes.guess_type(destination_path)
            if not content_type:
                content_type = "application/octet-stream"

            res = self.supabase.storage.from_(self.bucket_name).upload(
                path=destination_path,
                file=file_content,
                file_options={
                    "cache-control": "3600", 
                    "upsert": "true",
                    "content-type": content_type
                }
            )
            
            # Récupérer l'URL publique
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(destination_path)
            return public_url
            
        except Exception as e:
            print(f"❌ Erreur Supabase Storage : {e}")
            return None

storage_manager = SupabaseStorageManager()
