import json
import csv

input_file = r'c:\Users\mento\OneDrive\Desktop\phoneNumber\mca_debtors_enriched_full.json'
output_json = r'c:\Users\mento\OneDrive\Desktop\phoneNumber\debtors_with_phones.json'
output_csv = r'c:\Users\mento\OneDrive\Desktop\phoneNumber\debtors_with_phones.csv'

def extract_phones():
    print("Loading large JSON file...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    debtors = data.get('debtors', [])
    with_phones = [d for d in debtors if d.get('small_bizz_phones')]
    
    print(f"Found {len(with_phones)} records with phone numbers.")
    
    # Save as JSON
    with open(output_json, 'w') as f:
        json.dump(with_phones, f, indent=2)
    print(f"Saved to {output_json}")
    
    # Save as CSV for easier viewing (Excel/Table format)
    if with_phones:
        # Define the order of columns for the table
        keys = ["debtor_name", "Primary Phone", "All Phones", "sunbiz_email", "city", "state", "address", "zip", "num_mcas", "enhanced_distress_level"]
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            
            for d in with_phones:
                # Clean up the data for the CSV
                row = {
                    "debtor_name": d.get("debtor_name", ""),
                    "Primary Phone": d["small_bizz_phones"][0] if d.get("small_bizz_phones") else "",
                    "All Phones": "; ".join(d.get("small_bizz_phones", [])),
                    "sunbiz_email": d.get("sunbiz_email", "") or "",
                    "city": d.get("city", ""),
                    "state": d.get("state", ""),
                    "address": d.get("address", ""),
                    "zip": d.get("zip", ""),
                    "num_mcas": d.get("num_mcas", 0),
                    "enhanced_distress_level": d.get("enhanced_distress_level", "")
                }
                writer.writerow(row)
        print(f"Sorted and updated CSV saved to {output_csv}")

if __name__ == "__main__":
    extract_phones()
