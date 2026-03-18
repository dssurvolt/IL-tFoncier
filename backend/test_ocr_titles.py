from utils.land_title_extractor import extract_land_title_data
import os
import json

def test_land_title_extraction():
    title_dir = "/home/st4rk_18/st4rk_18-Projects/Ilot_foncier/titres"
    files = [
        "6231311b0abe3989951589.jpg",
        "6231762c8cd51798056129.jpg"
    ]
    
    for filename in files:
        filepath = os.path.join(title_dir, filename)
        if not os.path.exists(filepath):
            continue
            
        print(f"\n--- Testing Extraction on: {filename} ---")
        result = extract_land_title_data(filepath)
        # Ne pas afficher le raw_text pour la clarté
        if 'raw_text' in result: del result['raw_text']
        print(json.dumps(result, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    test_land_title_extraction()
