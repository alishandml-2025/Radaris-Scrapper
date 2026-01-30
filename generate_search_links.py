import json
import csv
import urllib.parse
from pathlib import Path

def generate_radaris_links():
    """
    Reads the extracted debtors JSON and generates a CSV with Radaris search links.
    """
    input_file = Path(r'c:\Users\mento\OneDrive\Desktop\phoneNumber\extracted_debtors_with_owners.json')
    output_file = Path(r'c:\Users\mento\OneDrive\Desktop\phoneNumber\radaris_search_queue.csv')

    if not input_file.exists():
        print(f"Error: {input_file} not found. Please run extract_debtors.py first.")
        return

    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Generating search links for {len(data)} companies...")
    
    # Define headers for the output CSV
    headers = ['Owner Name', 'Company Name', 'City', 'State', 'Zip', 'Radaris Search URL']
    
    rows = []
    seen_owners = set()
    for entry in data:
        company_name = entry.get('sunbiz_name', '')
        city = entry.get('city', '')
        state = entry.get('state', '')
        zip_code = entry.get('zip', '')
        owners = entry.get('sunbiz_owners', [])

        for owner in owners:
            if not owner:
                continue
            
            # De-duplication check
            unique_key = (owner.strip().upper(), city.strip().upper(), state.strip().upper())
            if unique_key in seen_owners:
                continue
            seen_owners.add(unique_key)
                
            # Reverting to working format: https://radaris.com/ng/search?ff=First&fl=Last&where=City, State
            name_parts = owner.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
            else:
                first_name = owner
                last_name = ""

            params = {
                "ff": first_name,
                "fl": last_name,
                "where": f"{city}, {state}".strip(", ")
            }
            query_string = urllib.parse.urlencode(params)
            search_url = f"https://radaris.com/ng/search?{query_string}"

            rows.append({
                'Owner Name': owner,
                'Company Name': company_name,
                'City': city,
                'State': state,
                'Zip': zip_code,
                'Radaris Search URL': search_url
            })

    print(f"Writing {len(rows)} search links to {output_file}...")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print("Done! You can now use the CSV to open search links or feed it to a scraper.")

if __name__ == "__main__":
    generate_radaris_links()
