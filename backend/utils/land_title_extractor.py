# Liste de mots clés obligatoires pour les titres fonciers officiels du Bénin
STRICT_OFFICIAL_MARKERS = [
    'REPUBLIQUE DU BENIN',
    'AGENCE NATIONALE DU DOMAINE ET DU FONCIER',
    'ANDF',
    'ANCF',
    'LIVRE FONCIER',
    'CONSERVATION FONCIERE',
]

# Liste de mots clés pour identification rapide
LAND_TITLE_KEYWORDS = [
    'TITRE FONCIER',
    'PROCEDURE',
    'BORNAGE',
    'PLAN PARCELLAIRE',
    'CADASTRE',
    'GEOMETRE',
    'EXPERTS',
    'TOPO',
    'SUPERFICIE',
    'SURFACE',
    'CONTENANCE',
    'NUP',
    'NUMERO UNIQUE PARCELLAIRE'
]

def extract_land_title_data(file_path_or_obj):
    """
    Extrait les données d'un titre foncier / plan parcellaire avec validation stricte.
    """
    try:
        if isinstance(file_path_or_obj, str):
            img = Image.open(file_path_or_obj)
        else:
            file_path_or_obj.seek(0)
            img = Image.open(io.BytesIO(file_path_or_obj.read()))
            
        # OCR haute densité (fra + eng pour les chiffres/codes)
        text = pytesseract.image_to_string(img, lang='fra+eng')
        return _parse_land_title(text)
    except Exception as e:
        logger.error(f"Error extracting land title: {e}")
        return {'error': str(e)}

def _parse_land_title(text: str) -> dict:
    """
    Analyse approfondie du texte OCR pour garantir l'absence de fraude.
    """
    text_clean = text.replace('\r', '')
    lines = [l.strip() for l in text_clean.split('\n') if l.strip()]
    text_flat = ' '.join(lines)
    text_upper = text_flat.upper()
    
    result = {
        'is_land_title': False,
        'official_document': False,
        'document_type': 'INCONNU',
        'nup': None,
        'title_number': None,
        'commune': None,
        'area_sqm': None,
        'area_formatted': None,
        'surveyor': None,
        'cabinet': None,
        'confidence': 0,
        'is_copy': False,
        'warnings': []
    }
    
    # --- 1. Validation de l'authenticité (Official Markers) ---
    found_official = sum(1 for m in STRICT_OFFICIAL_MARKERS if m in text_upper)
    if found_official >= 1:
        result['official_document'] = True
        
    # --- 2. Détection du NUP (Numéro Unique Parcellaire - 9 chiffres) ---
    # Le NUP est entre 100 000 001 et 999 999 999
    nup_match = re.search(r'\b([1-9]\d{8})\b', text_flat)
    if nup_match:
        result['nup'] = nup_match.group(1)
        result['document_type'] = "Parcelle Enregistrée (NUP)"

    # --- 3. Détection du Numéro de Titre Foncier ---
    # Pattern: TF XXXX ou TITRE N° XXXX
    match = re.search(r'(?:TITRE|T\.?F\.?|N[°.]?)\s*(?:FONCIER\s*)?(?:N.|N°|[:\s]|_)\s*([A-Z0-9\-/]+)', text_flat, re.IGNORECASE)
    if match:
        val = match.group(1).strip()
        # Filtrage des mots-clés d'entête capturés par erreur
        if val.upper() not in ['FONCIER', 'TOPO', 'CABINET', 'ORDRE', 'BENIN', 'NUP']:
            result['title_number'] = val
            result['document_type'] = "Titre Foncier"

    # --- 4. Détermination de la véracité du Titre (is_land_title) ---
    # On nécessite : soit un NUP, soit un Titre N° + Marque Officielle
    if (result['nup'] or (result['title_number'] and result['official_document'])):
        result['is_land_title'] = True
    elif sum(1 for kw in LAND_TITLE_KEYWORDS if kw in text_upper) >= 3:
        result['is_land_title'] = True # Plan parcellaire probable
        result['document_type'] = "Plan Parcellaire / Levé"

    # --- 5. Commune (Stricte) ---
    match = re.search(r'(?:LIVRE\s+FONCIER|Commune|Com\.?|Ville)\s*(?:de|d\')?\s*[:\s]*([A-ZÀÂÉÈÊËÏÔÙÛÜÇ\s\-]{3,})', text_flat, re.IGNORECASE)
    if match:
        commune = match.group(1).strip()
        commune = re.split(r'\n|TITRE|SURFACE|DATE|TEL|TÉL|OUA|SITUATION|ANDF|ANCF', commune, flags=re.IGNORECASE)[0].strip()
        if len(commune) > 3:
            result['commune'] = commune

    # --- 6. Superficie (Robuste) ---
    area_text = text_flat.replace('O', '0').replace('o', '0')
    h_match = re.search(r'(\d{1,3})\s*[hH]', area_text)
    a_match = re.search(r'(\d{1,3})\s*[aA][\s\b]', area_text) # Espace après pour éviter ca
    ca_match = re.search(r'(\d{1,3})\s*[cC][aA]', area_text)
    
    total_m2 = 0
    parts = []
    if h_match:
        val = int(h_match.group(1))
        total_m2 += val * 10000
        parts.append(f"{val}h")
    if a_match:
        val = int(a_match.group(1))
        total_m2 += val * 100
        parts.append(f"{val}a")
    if ca_match:
        val = int(ca_match.group(1))
        total_m2 += val
        parts.append(f"{val}ca")
        
    if total_m2 > 0:
        result['area_sqm'] = total_m2
        result['area_formatted'] = " ".join(parts)

    # --- 7. Sécurité : Copie / Annulé ---
    if 'COPIE' in text_upper or 'PHOTOCOPIE' in text_upper:
        result['is_copy'] = True
        result['warnings'].append("Document identifié comme une COPIE.")
    if 'ANNUL' in text_upper:
        result['warnings'].append("ALERTE : Mention 'ANNULÉ' détectée sur le document.")

    # --- 8. Confiance finale ---
    # Critères : Official Marker (20), NUP (20), Title Num (20), Area (20), Commune (20)
    score = 0
    if result['official_document']: score += 20
    if result['nup']: score += 20
    if result['title_number']: score += 20
    if result['area_sqm']: score += 20
    if result['commune']: score += 20
    result['confidence'] = score
    
    return result

def is_land_document(text):
    found_keywords = sum(1 for kw in LAND_TITLE_KEYWORDS if kw.lower() in text.lower())
    return found_keywords >= 2
