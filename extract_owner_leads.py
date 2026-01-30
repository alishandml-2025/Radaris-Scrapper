import json
import os
import csv
from pathlib import Path

# Paths
base_dir = Path(r'c:\Users\mento\OneDrive\Desktop\phoneNumber')
input_file = base_dir / 'mca_debtors_enriched_full.json'
chunks_dir = base_dir / 'sunbiz_entities_chunks_200'
output_csv = base_dir / 'owner_skip_tracing_leads.csv'

def extract_owner_links():
    print("Loading debtors data...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {input_file}: {e}")
        return

    debtors = data.get('debtors', [])
    
    # Map doc number to full debtor data for context
    doc_to_debtor_data = {}
    for d in debtors:
        doc_num = d.get('sunbiz_doc_num')
        if doc_num:
            doc_to_debtor_data[doc_num.upper()] = d

    print(f"Tracking {len(doc_to_debtor_data)} document numbers from debtors.")

    # Leads list
    leads = []
    seen_leads = set() # To avoid duplicates (Name + Address)

    # Scan chunks (Primary Source)
    chunk_files = list(chunks_dir.glob('*.json'))
    if chunk_files:
        print(f"Scanning {len(chunk_files)} Sunbiz chunks for detailed officer data...")
        for chunk_path in chunk_files:
            try:
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
            except:
                continue

            for entity in chunk_data:
                doc_num = entity.get('id', '').upper()
                if doc_num in doc_to_debtor_data:
                    debtor_data = doc_to_debtor_data[doc_num]
                    debtor_name = debtor_data.get('debtor_name')
                    officers = entity.get('officers', [])
                    
                    for off in officers:
                        name = off.get('name', '').strip()
                        addr = off.get('address', {})
                        
                        if not name or not addr:
                            continue
                            
                        # Create a unique key for deduplication
                        line1 = addr.get('line1', '').strip()
                        city = addr.get('city', '').strip()
                        state = addr.get('state', '').strip()
                        zip_code = addr.get('zip', '').strip()
                        
                        lead_key = f"{name}|{line1}|{zip_code}".upper()
                        
                        if lead_key not in seen_leads:
                            leads.append({
                                "Owner Name": name,
                                "Street Address": line1,
                                "City": city,
                                "State": state,
                                "Zip": zip_code,
                                "Company Name": debtor_name,
                                "Title": off.get('title', ''),
                                "Sunbiz ID": doc_num
                            })
                            seen_leads.add(lead_key)

    print(f"Extracted {len(leads)} unique owner leads from Sunbiz chunks.")

    # Save to CSV
    if leads:
        headers = ["Owner Name", "Street Address", "City", "State", "Zip", "Company Name", "Title", "Sunbiz ID"]
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(leads)
        print(f"Skip tracing leads saved to {output_csv}")
    else:
        print("No leads found in Sunbiz chunks.")

if __name__ == "__main__":
    extract_owner_links()
