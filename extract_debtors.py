import json
import os

def extract_debtor_data(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    debtors = data.get('debtors', [])
    extracted_data = []

    print(f"Processing {len(debtors)} debtors...")
    for debtor in debtors:
        # Check if sunbiz_owners exists and is not empty
        owners = debtor.get('sunbiz_owners')
        if not owners: # Skip if None or empty list
            continue

        # Extract requested fields
        entry = {
            "sunbiz_name": debtor.get('sunbiz_name'),
            "sunbiz_email": debtor.get('sunbiz_email'),
            "sunbiz_owners": owners,
            "sunboz_doc_number": debtor.get('sunbiz_doc_num'), # Mapped as requested
            "city": debtor.get('city'),
            "state": debtor.get('state'),
            "address": debtor.get('address'),
            "zip": debtor.get('zip')
        }
        extracted_data.append(entry)

    print(f"Extracted {len(extracted_data)} debtors with owners.")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2)
    
    print(f"Saved extracted data to {output_file}")

if __name__ == "__main__":
    input_path = r'c:\Users\mento\OneDrive\Desktop\phoneNumber\mca_debtors_enriched_full.json'
    output_path = r'c:\Users\mento\OneDrive\Desktop\phoneNumber\extracted_debtors_with_owners.json'
    extract_debtor_data(input_path, output_path)
