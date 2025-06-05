import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def extract_internship_details(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    details = {}

    # Job description & details
    job_details_div = soup.select_one("div.internship_details > div.text-container")
    details['job_description'] = job_details_div.get_text(separator="\n").strip() if job_details_div else None

    # Skills required
    skills_spans = soup.select("div.round_tabs_container span.round_tabs")
    skills = [span.text.strip() for span in skills_spans]
    details['skills'] = skills

    # Number of openings
    openings_heading = soup.find("h3", text="Number of openings")
    if openings_heading:
        openings_div = openings_heading.find_next_sibling("div", class_="text-container")
        details['openings'] = openings_div.text.strip() if openings_div else None
    else:
        details['openings'] = None

    # Perks
    perks_heading = soup.find("h3", text="Perks")
    if perks_heading:
        perks_spans = perks_heading.find_next_sibling("div", class_="round_tabs_container").select("span.round_tabs")
        perks = [span.text.strip() for span in perks_spans]
        details['perks'] = perks
    else:
        details['perks'] = None

    # Company website link
    website_a = soup.select_one("div.website_link a")
    details['company_website'] = website_a['href'] if website_a else None

    # Company about text
    about_div = soup.select_one("div.about_company_text_container")
    details['company_about'] = about_div.text.strip() if about_div else None

    return details

def scrape_internships(csv_path):
    df = pd.read_csv(csv_path)

    # Clean company column if it contains line breaks
    df['company'] = df['company'].str.replace('\n', ' ', regex=False).str.strip()

    results = []

    for idx, row in df.iterrows():
        print(f"Scraping {idx+1}/{len(df)}: {row['role']} at {row['company']}")
        url = row['link']

        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200:
                details = extract_internship_details(response.text)
            else:
                print(f"Failed to fetch page for {row['role']}: Status code {response.status_code}")
                details = {}
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            details = {}

        # Combine all data into one dictionary
        data = {
            "role": row['role'],
            "company": row['company'],
            "stipend": row['stipend'],
            "link": url,
            **details
        }

        results.append(data)

        # Be polite, don't hammer the server
        time.sleep(2)

    return pd.DataFrame(results)

def run_detail_scraper(input_csv_path="data/joblisting/internships.csv", output_csv_path="data/joblisting/internships_scraped.csv"):
    df_scraped = scrape_internships(input_csv_path)
    df_scraped.to_csv(output_csv_path, index=False)
    print(f"Scraping complete. Data saved to {output_csv_path}")
    return df_scraped

