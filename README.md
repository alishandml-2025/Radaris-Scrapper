# Florida Business Owner Skip Tracing & Lead Enrichment

This repository contains a set of tools designed to identify Florida business owners from debtor lists, cross-reference them with Sunbiz (Florida Department of State) records to find their personal details, and automate verify phone numbers using Radaris.

## 🚀 Key Features

*   **Sunbiz Integration:** Enriches debtor data by matching business names with Florida's official Sunbiz registry to find real owner names and home addresses.
*   **Automated Skip Tracing:** Uses Playwright to scrape Radaris for phone numbers associated with the identified business owners.
*   **Intelligent Matching:** Implements scoring logic to verify that the person found matches the target's city and state.
*   **Data Enrichment:** Outputs clean CSV/JSON files ready for cold calling or marketing campaigns.

## 📂 Project Structure

*   `extract_owner_leads.py`: **[Step 1]** Matches your raw debtor list (`mca_debtors_enriched_full.json`) with Sunbiz data chunks to extract owner names and home addresses.
*   `radaris_scraper.py`: **[Step 2]** Takes the output from Step 1, searches Radaris for each owner, and saves potential phone numbers.
*   `extract_phones.py` / `extract_owner_phones.py`: Helper scripts to parse and clean extracted phone number data.
*   `mca_debtors_enriched_full.json`: Input dataset containing the initial list of debtors.
*   `Sun-Biz-Aggregator/`: Submodule/folder containing logic for fetching raw Sunbiz data.

## 🛠️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/alishandml-2025/Radaris-Scrapper.git
    cd Radaris-Scrapper
    ```

2.  **Install Dependencies:**
    This project requires Python and Playwright.
    ```bash
    pip install playwright
    playwright install chromium
    ```

## ⚡ Usage

### 1. Extract Owner Leads
Generate a list of targets by cross-referencing your debtors with Sunbiz data.
```bash
python extract_owner_leads.py
```
*Output: `owner_skip_tracing_leads.csv`*

### 2. Run the Radaris Scraper
Feed the leads into the scraper to find phone numbers.
```bash
python radaris_scraper.py
```
*   Config: You can adjust `BATCH_SIZE` and `MAX_CONCURRENT_PAGES` inside the script.
*   Output: `radaris_test_results.json`

## ⚠️ Disclaimer
This tool is for educational and data enrichment purposes. Ensure you comply with all local laws regarding data scraping and privacy (e.g., TCPA, GDPR) when using extracted contact information.
