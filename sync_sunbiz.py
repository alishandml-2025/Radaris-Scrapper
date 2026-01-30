import json
import os
import csv

# Paths
base_dir = r'c:\Users\mento\OneDrive\Desktop\phoneNumber'
debtors_file = os.path.join(base_dir, 'debtors_with_phones.json')
chunks_dir = os.path.join(base_dir, 'sunbiz_entities_chunks_200')
output_file = os.path.join(base_dir, 'debtors_super_enriched.json')
output_csv = os.path.join(base_dir, 'debtors_super_enriched.csv')

def sync_data():
    print("Loading debtors...")
    with open(debtors_file, 'r', encoding='utf-8') as f:
        debtors = json.load(f)
    
    # Create lookup map for doc numbers
    doc_num_map = {}
    for i, d in enumerate(debtors):
        doc_num = d.get('sunbiz_doc_num')
        if doc_num:
            # Document numbers in Sunbiz chunks are uppercase, sometimes without leading zero 
            # but usually they match. We'll store the index.
            doc_num_map[doc_num.upper()] = i
            
    print(f"Tracking {len(doc_num_map)} unique Sunbiz document numbers from debtors.")
    
    # Iterate through all 1290 chunks
    chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.json')]
    count_matched = 0
    
    print(f"Scanning {len(chunk_files)} Sunbiz chunks for matches...")
    
    for filename in chunk_files:
        chunk_path = os.path.join(chunks_dir, filename)
        with open(chunk_path, 'r', encoding='utf-8') as f:
            try:
                chunk_data = json.load(f)
            except:
                continue
                
            for entity in chunk_data:
                entity_id = entity.get('id', '').upper()
                if entity_id in doc_num_map:
                    idx = doc_num_map[entity_id]
                    # We found a match! Add the extra details
                    debtors[idx]['sunbiz_details'] = {
                        'date_filed': entity.get('date_filed'),
                        'agent': entity.get('agent'),
                        'detailed_officers': entity.get('officers'),
                        'address_principal': entity.get('address_principal'),
                        'address_mailing': entity.get('address_mailing'),
                        'ein': entity.get('ein')
                    }
                    count_matched += 1
    
    print(f"Successfully synced {count_matched} deep records from Sunbiz chunks.")
    
    # Save JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(debtors, f, indent=2)
        
    # Save CSV with the new columns
    if debtors:
        # Define the order of columns, adding the new synced data
        keys = [
            "debtor_name", 
            "Primary Phone", 
            "sunbiz_email", 
            "Agent Name",
            "Agent Address",
            "Filing Date",
            "Principal Address",
            "Officer Names",
            "enhanced_distress_level",
            "city", 
            "sunbiz_doc_num"
        ]
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            
            for d in debtors:
                details = d.get('sunbiz_details', {})
                agent = details.get('agent', {})
                agent_addr = agent.get('address', {})
                p_addr = details.get('address_principal', {})
                
                # Format officers as a string
                officers = "; ".join([f"{off.get('title')}: {off.get('name')}" for off in details.get('detailed_officers', [])])
                
                row = {
                    "debtor_name": d.get("debtor_name", ""),
                    "Primary Phone": d.get("small_bizz_phones", [""])[0] if d.get("small_bizz_phones") else "",
                    "sunbiz_email": d.get("sunbiz_email", "") or "",
                    "Agent Name": agent.get('name', ''),
                    "Agent Address": f"{agent_addr.get('line1', '')}, {agent_addr.get('city', '')} {agent_addr.get('zip', '')}",
                    "Filing Date": details.get('date_filed', ''),
                    "Principal Address": f"{p_addr.get('line1', '')}, {p_addr.get('city', '')} {p_addr.get('zip', '')}",
                    "Officer Names": officers or ", ".join(d.get('sunbiz_owners', [])),
                    "enhanced_distress_level": d.get("enhanced_distress_level", ""),
                    "city": d.get("city", ""),
                    "sunbiz_doc_num": d.get("sunbiz_doc_num", "")
                }
                writer.writerow(row)
        print(f"Super-Enriched CSV saved to {output_csv}")

if __name__ == "__main__":
    sync_data()
