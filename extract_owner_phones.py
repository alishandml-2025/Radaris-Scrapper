import json
import csv
from pathlib import Path

# Paths
base_dir = Path(r'c:\Users\mento\OneDrive\Desktop\phoneNumber')
input_file = base_dir / 'mca_debtors_enriched_full.json'
chunks_dir = base_dir / 'sunbiz_entities_chunks_200'
output_csv = base_dir / 'owner_phones_output.csv'

def extract_owner_phones():
    print(f"Loading debtors data from {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {input_file}: {e}")
        return

    debtors = data.get('debtors', [])
    
    # Map doc number to phone and other info
    # We only care about debtors with phones
    doc_to_info = {}
    for d in debtors:
        doc_num = d.get('sunbiz_doc_num')
        phones = d.get('small_bizz_phones', [])
        if doc_num and phones:
            doc_to_info[doc_num.upper()] = {
                "phones": phones,
                "email": d.get('sunbiz_email') or (d.get('small_bizz_emails')[0] if d.get('small_bizz_emails') else ""),
                "company_name": d.get('debtor_name'),
                "city": d.get('city'),
                "state": d.get('state'),
                "zip": d.get('zip')
            }

    print(f"Tracking {len(doc_to_info)} debtors with phone numbers.")

    leads = []
    seen_keys = set()

    # Scan Sunbiz chunks for officer details
    chunk_files = list(chunks_dir.glob('*.json'))
    if chunk_files:
        print(f"Scanning {len(chunk_files)} Sunbiz chunks for officer details...")
        for chunk_path in chunk_files:
            try:
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
            except:
                continue

            for entity in chunk_data:
                doc_num = entity.get('id', '').upper()
                if doc_num in doc_to_info:
                    info = doc_to_info[doc_num]
                    officers = entity.get('officers', [])
                    
                    for off in officers:
                        name = off.get('name', '').strip()
                        if not name:
                            continue
                            
                        # Extract address from officer record if available
                        addr = off.get('address', {})
                        line1 = addr.get('line1', '').strip()
                        city = addr.get('city', '').strip()
                        state = addr.get('state', '').strip()
                        zip_code = addr.get('zip', '').strip()
                        
                        # Use business address as fallback if officer address is missing
                        if not line1:
                            # Actually, we want specific officer details if possible
                            # But if the chunk doesn't have it, we might skip or use business addr
                            pass

                        for phone in info['phones']:
                            lead_key = f"{name}|{line1}|{phone}".upper()
                            if lead_key not in seen_keys:
                                leads.append({
                                    "Owner Name": name,
                                    "Title": off.get('title', ''),
                                    "Phone": phone,
                                    "Email": info['email'],
                                    "Company Name": info['company_name'],
                                    "Street Address": line1,
                                    "City": city,
                                    "State": state,
                                    "Zip": zip_code,
                                    "Sunbiz ID": doc_num
                                })
                                seen_keys.add(lead_key)

    print(f"Extracted {len(leads)} owner leads with phone numbers.")

    # Save to CSV
    if leads:
        headers = ["Owner Name", "Title", "Phone", "Email", "Company Name", "Street Address", "City", "State", "Zip", "Sunbiz ID"]
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(leads)
        print(f"Results saved to {output_csv}")
    else:
        print("No matches found.")

if __name__ == "__main__":
    extract_owner_phones()
