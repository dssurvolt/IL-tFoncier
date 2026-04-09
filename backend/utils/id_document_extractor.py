"""
Module d'extraction automatique des données d'identité à partir de documents scannés.
Supporte : PDF, JPG, PNG, WEBP
Documents ciblés : CIP (Certificat d'Identification Personnelle), CNI, Passeport béninois
"""
import re
import os
import logging
from io import BytesIO

import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

# Diagnostic path for Render/Linux
TESSERACT_CMD = os.getenv('TESSERACT_CMD', 'tesseract')
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Mois français → numéro
MOIS_FR = {
    'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
    'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
    'aout': '08', 'septembre': '09', 'octobre': '10', 'novembre': '11',
    'décembre': '12', 'decembre': '12',
    'fevrier': '02',
}


def extract_from_file(file_path: str) -> dict:
    """
    Extrait les informations d'identité depuis un fichier (PDF ou Image).
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return _extract_from_pdf(file_path)
    elif ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'):
        return _extract_from_image_path(file_path)
    else:
        return {'error': f"Format de fichier non supporté : {ext}"}


def extract_from_upload(uploaded_file) -> dict:
    """
    Extrait les informations d'identité depuis un fichier uploadé (Django UploadedFile).
    Gère automatiquement PDF et images.
    """
    content_type = uploaded_file.content_type or ''
    file_name = uploaded_file.name or ''
    ext = os.path.splitext(file_name)[1].lower()
    
    try:
        file_bytes = uploaded_file.read()
        
        if ext == '.pdf' or 'pdf' in content_type:
            return _extract_from_pdf_bytes(file_bytes)
        else:
            return _extract_from_image_bytes(file_bytes)
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction : {e}")
        return {'error': str(e)}


def _extract_from_pdf(file_path: str) -> dict:
    """Extrait depuis un fichier PDF sur le disque."""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(file_path, dpi=300)
        if not images:
            return {'error': 'Le PDF est vide ou illisible.'}
        return _process_image(images[0])
    except Exception as e:
        logger.error(f"Erreur conversion PDF : {e}")
        return {'error': f"PDF illisible : {str(e)}"}


def _extract_from_pdf_bytes(file_bytes: bytes) -> dict:
    """Extrait depuis des bytes d'un PDF uploadé."""
    try:
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(file_bytes, dpi=300)
        if not images:
            return {'error': 'Le PDF est vide ou illisible.'}
        return _process_image(images[0])
    except Exception as e:
        logger.error(f"Erreur conversion PDF (bytes) : {e}")
        return {'error': f"PDF illisible : {str(e)}"}


def _extract_from_image_path(file_path: str) -> dict:
    """Extrait depuis un fichier image sur le disque."""
    try:
        img = Image.open(file_path)
        return _process_image(img)
    except Exception as e:
        logger.error(f"Erreur ouverture image : {e}")
        return {'error': f"Image illisible : {str(e)}"}


def _extract_from_image_bytes(file_bytes: bytes) -> dict:
    """Extrait depuis des bytes d'une image uploadée."""
    try:
        img = Image.open(BytesIO(file_bytes))
        return _process_image(img)
    except Exception as e:
        logger.error(f"Erreur ouverture image (bytes) : {e}")
        return {'error': f"Image illisible : {str(e)}"}


def _process_image(img: Image.Image) -> dict:
    """
    Pipeline principal : Image → OCR → Parsing → Données structurées.
    """
    try:
        try:
            raw_text = pytesseract.image_to_string(img, lang='fra')
        except Exception as e:
            logger.warning(f"OCR en français a échoué, tentative sans langue spécifique: {e}")
            raw_text = pytesseract.image_to_string(img)
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract n'est pas installé ou n'est pas dans le PATH.")
        return {
            'error': "Erreur d'analyse : Tesseract OCR n'est pas installé sur le serveur. "
                     "Veuillez installer 'tesseract-ocr' et 'tesseract-ocr-fra' via votre script de build "
                     "(ex: apt-get install tesseract-ocr)."
        }
    except Exception as e:
        logger.error(f"Erreur technique lors de l'OCR : {e}")
        return {'error': f"Erreur technique lors du traitement de l'image : {str(e)}"}
    
    logger.info(f"Texte OCR extrait ({len(raw_text)} chars)")
    
    data = _parse_benin_id(raw_text)
    data['raw_text'] = raw_text
    
    return data


def _parse_benin_id(text: str) -> dict:
    """
    Parse le texte OCR pour extraire les champs d'un document d'identité béninois.
    Supporte CIP, CNI, Passeport.
    
    Stratégie: On travaille à la fois sur le texte ligne-par-ligne et le texte aplati
    pour capturer tous les cas de figure de l'OCR.
    """
    result = {
        'document_type': _detect_document_type(text),
        'document_number': None,
        'id_number': None,
        'last_name': None,
        'first_name': None,
        'birth_date': None,
        'birth_place': None,
        'nationality': None,
        'phone': None,
        'gender': None,
        'father_name': None,
        'mother_name': None,
        'address': None,
        'expiry_date': None,
        'confidence': 0
    }
    
    # Deux versions du texte pour maximiser la capture
    lines = [l.strip() for l in text.replace('\r', '').split('\n') if l.strip()]
    text_flat = ' '.join(lines)
    
    # ===== 1. Numéro du document (N° en haut du CIP) =====
    match = re.search(r'N[°o]?\s*(\d{10,15})', text_flat)
    if match:
        result['document_number'] = match.group(1)
    
    # ===== 2. Numéro Personnel d'Identification (NPI) =====
    match = re.search(r"(?:Personnel\s+d.?[Ii]dentification|NPI)\s*[:\s]*(\d{5,15})", text_flat)
    if match:
        result['id_number'] = match.group(1)
    
    # ===== 3. Nom =====
    # Cherche "Nom : VALEUR" sur la même ligne ou le texte aplati
    match = re.search(r'Nom\s*:\s*([A-ZÀÂÉÈÊËÏÔÙÛÜÇa-zàâéèêëïôùûüç\s\.\-]+?)(?:\n|Pr[ée]nom)', text)
    if match:
        nom = re.sub(r'\s+', ' ', match.group(1).strip())
        if len(nom) > 1:
            result['last_name'] = nom
    
    if not result['last_name']:
        for line in lines:
            m = re.match(r'Nom\s*:\s*(.+)', line)
            if m:
                nom = m.group(1).strip()
                if len(nom) > 1:
                    result['last_name'] = nom
                break
    
    # ===== 4. Prénom(s) =====
    match = re.search(r'Pr[ée]nom\s*\(?s?\)?\s*:\s*([A-ZÀÂÉÈÊËÏÔÙÛÜÇa-zàâéèêëïôùûüç\s\.\-]+?)(?:\n|Date)', text)
    if match:
        prenom = re.sub(r'\s+', ' ', match.group(1).strip())
        if len(prenom) > 1:
            result['first_name'] = prenom
    
    if not result['first_name']:
        for line in lines:
            m = re.match(r'Pr[ée]nom\s*\(?s?\)?\s*:\s*(.+)', line)
            if m:
                prenom = m.group(1).strip()
                if len(prenom) > 1:
                    result['first_name'] = prenom
                break
    
    # ===== 5. Date de naissance =====
    # Format texte français : "19 avril 2006"
    match = re.search(r'Date\s+de\s+naissance\s*:\s*(\d{1,2})\s+([a-zéûôàâè]+)\s+(\d{4})', text_flat, re.IGNORECASE)
    if match:
        jour = match.group(1).zfill(2)
        mois_txt = match.group(2).lower()
        annee = match.group(3)
        mois = MOIS_FR.get(mois_txt, '01')
        result['birth_date'] = f"{annee}-{mois}-{jour}"
    else:
        # Format numérique : "19/04/2006" ou "19-04-2006"
        match = re.search(r'Date\s+de\s+naissance\s*:\s*(\d{2})[/\-](\d{2})[/\-](\d{4})', text_flat)
        if match:
            result['birth_date'] = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    
    # ===== 6. Lieu de naissance =====
    # Sur le CIP, le lieu apparaît souvent comme "Lieu de naissance : Com. : PARAKOU" 
    # mais l'OCR peut séparer le label de la valeur.
    
    # Approche 1 : Chercher "Lieu de naissance : VALEUR" sur une même ligne
    for line in lines:
        m = re.search(r'Lieu\s+de\s+naissance\s*:\s*(?:Com\.?\s*:\s*)?(.+)', line, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if len(val) > 2 and 'Nationalit' not in val:
                result['birth_place'] = val
            break
    
    # Approche 2 : Si vide, chercher le "Com. : NOM" qui suit immédiatement
    if not result['birth_place']:
        for i, line in enumerate(lines):
            if 'Lieu de naissance' in line:
                # Regarder les lignes suivantes pour trouver "Com. : PARAKOU"
                for j in range(i + 1, min(i + 4, len(lines))):
                    m = re.search(r'Com\.?\s*:\s*([A-ZÀÂÉÈÊËÏÔÙÛÜÇ]{3,})', lines[j])
                    if m:
                        result['birth_place'] = m.group(1).strip()
                        break
                    # Si la ligne est un lieu simple (pas un label connu)
                    if lines[j] and not re.match(r'(Nationalit|Num[ée]ro|Adresse|Et\s)', lines[j]):
                        val = re.sub(r'^Com\.?\s*:\s*', '', lines[j]).strip()
                        if len(val) > 2:
                            result['birth_place'] = val
                            break
                break
    
    # Approche 3 : Dans le CIP, "Com. : PARAKOU" apparaît parfois juste après le numéro de téléphone
    # On cherche le pattern "Com. : NOM_EN_MAJUSCULES" en excluant l'adresse de résidence (COTONOU)
    if not result['birth_place']:
        com_matches = re.findall(r'Com\.?\s*:\s*([A-ZÀÂÉÈÊËÏÔÙÛÜÇ]{3,})', text_flat)
        # S'il y a 2 communes, la 2ème est souvent le lieu de naissance (la 1ère est l'adresse)
        if len(com_matches) >= 2:
            result['birth_place'] = com_matches[1]
        elif len(com_matches) == 1:
            result['birth_place'] = com_matches[0]
    
    # Nettoyage final : si birth_place contient des artefacts
    if result['birth_place']:
        bp = result['birth_place']
        bp = re.sub(r'Nationalit[ée]?\s*:?.*', '', bp, flags=re.IGNORECASE).strip()
        bp = re.sub(r'\s+', ' ', bp).strip()
        if len(bp) < 2:
            result['birth_place'] = None
        else:
            result['birth_place'] = bp
    
    # ===== 7. Nationalité =====
    match = re.search(r'Nationalit[ée]\s*:\s*([A-ZÉÈÊËÀÂÙÛÜÎÏÇa-zéèêëàâùûüîïç]+)', text_flat, re.IGNORECASE)
    if match:
        nat = match.group(1).strip()
        # Filtrer les artefacts OCR comme "Et" ou "LP"
        if len(nat) > 3:
            result['nationality'] = nat.upper()
    
    # Si la nationalité est courte ou absente, chercher "BÉNIN" ou "BÉNINOISE" dans le contexte
    if not result['nationality']:
        if re.search(r'B[ÉE]NIN', text_flat, re.IGNORECASE):
            result['nationality'] = 'BÉNINOISE'
    
    # ===== 8. Téléphone =====
    # Chercher le pattern "+229 XXXXXXXXXX" ou juste un numéro après "téléphone"
    match = re.search(r'(?:t[ée]l[ée]phone|T[ée]l)\s*:\s*(\+?\d[\d\s]{8,15})', text_flat, re.IGNORECASE)
    if match:
        phone = re.sub(r'\s+', '', match.group(1))
        result['phone'] = phone
    
    # Fallback : chercher un numéro béninois dans le texte (+229...)
    if not result['phone']:
        match = re.search(r'(\+229\s?\d[\d\s]{7,12})', text_flat)
        if match:
            result['phone'] = re.sub(r'\s+', '', match.group(1))
    
    # ===== 9. Sexe / Genre =====
    match = re.search(r'Sexe\s*:\s*(Masculin|F[ée]minin|M|F)', text_flat, re.IGNORECASE)
    if match:
        sexe = match.group(1).strip().upper()
        if sexe in ('MASCULIN', 'M'):
            result['gender'] = 'M'
        elif sexe in ('FEMININ', 'FÉMININ', 'F'):
            result['gender'] = 'F'
    
    # ===== 10. Père =====
    match = re.search(r'P[èe]re\s*:\s*([A-ZÀÂÉÈÊËÏÔÙÛÜÇa-zàâéèêëïôùûüç\s\.\-]+?)(?:\n|M[èe]re)', text, re.IGNORECASE)
    if match:
        result['father_name'] = re.sub(r'\s+', ' ', match.group(1).strip())
    
    if not result['father_name']:
        for line in lines:
            m = re.match(r'P[èe]re\s*:\s*(.+)', line, re.IGNORECASE)
            if m:
                result['father_name'] = m.group(1).strip()
                break
    
    # ===== 11. Mère =====
    match = re.search(r'M[èe]re\s*:\s*([A-ZÀÂÉÈÊËÏÔÙÛÜÇa-zàâéèêëïôùûüç\s\.\-]+?)(?:\n|Expire|Num[ée]ro|$)', text, re.IGNORECASE)
    if match:
        result['mother_name'] = re.sub(r'\s+', ' ', match.group(1).strip())
    
    if not result['mother_name']:
        for line in lines:
            m = re.match(r'M[èe]re\s*:\s*(.+)', line, re.IGNORECASE)
            if m:
                result['mother_name'] = m.group(1).strip()
                break
    
    # ===== 12. Adresse de résidence =====
    address_parts = []
    # Commune
    com_match = re.search(r'Com\.?\s*:\s*([A-ZÀÂÉÈÊËÏÔÙÛÜÇ][A-ZÀÂÉÈÊËÏÔÙÛÜÇa-z\s\-]+?)(?:\s*[/|]\s*Arr|$)', text_flat, re.IGNORECASE)
    if com_match:
        addr_com = com_match.group(1).strip()
        # S'assurer qu'on n'a pas pris le lieu de naissance
        if result.get('birth_place') and addr_com == result['birth_place']:
            # Chercher le 2ème "Com."
            matches = list(re.finditer(r'Com\.?\s*:\s*([A-ZÀÂÉÈÊËÏÔÙÛÜÇ][A-ZÀÂÉÈÊËÏÔÙÛÜÇa-z\s\-]+?)(?:\s*[/|]\s*Arr|$)', text_flat, re.IGNORECASE))
            if len(matches) > 1:
                address_parts.append(matches[1].group(1).strip())
        else:
            address_parts.append(addr_com)
    
    # Quartier
    qt_match = re.search(r'Qt\.?\s*:\s*([A-ZÀÂÉÈÊËÏÔÙÛÜÇ][A-ZÀÂÉÈÊËÏÔÙÛÜÇa-z\s\.\-]+?)(?:\n|Lieu|$)', text, re.IGNORECASE)
    if qt_match:
        address_parts.append(qt_match.group(1).strip())
    
    if address_parts:
        result['address'] = ', '.join(address_parts)
    
    # ===== 13. Date d'expiration =====
    match = re.search(r'Expire?\s*(?:le)?\s*:?\s*(\d{2})[/\-](\d{2})[/\-](\d{4})', text_flat)
    if match:
        result['expiry_date'] = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    
    # --- Calcul du score de confiance ---
    fields_found = sum(1 for k, v in result.items() if v and k not in ('document_type', 'confidence', 'raw_text'))
    total_fields = 13
    result['confidence'] = round((fields_found / total_fields) * 100)
    
    return result


def _detect_document_type(text: str) -> str:
    """Détecte le type de document d'identité."""
    text_upper = text.upper()
    
    if "CERTIFICAT D'IDENTIFICATION PERSONNELLE" in text_upper or "CERTIFICAT D'IDENTIFICA" in text_upper:
        return 'CIP'
    elif "CARTE NATIONALE D'IDENTITÉ" in text_upper or "CARTE NATIONALE" in text_upper:
        return 'CNI'
    elif 'PASSEPORT' in text_upper or 'PASSPORT' in text_upper:
        return 'PASSEPORT'
    elif 'RAVIP' in text_upper or 'RÉCÉPISSÉ' in text_upper:
        return 'RAVIP'
    elif 'PERMIS DE CONDUIRE' in text_upper:
        return 'PERMIS'
    else:
        return 'INCONNU'
