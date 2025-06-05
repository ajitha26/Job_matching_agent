import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import os
from collections import Counter

def extract_keywords_from_resume(file_path: str) -> list:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().lower()

    # Basic keyword candidates — you can enhance this later with NLP
    tokens = re.findall(r'\b[a-zA-Z][a-zA-Z0-9.+#]+\b', text)
    stopwords = {"and", "or", "in", "on", "the", "with", "a", "an", "to", "for", "of", "as", "at", "by", "is", "are"}
    
    # Filter out too generic terms and single-letter tokens
    keywords = [token for token in tokens if len(token) > 2 and token not in stopwords]

    # Count and return most common terms
    common = Counter(keywords).most_common(20)
    return [word for word, _ in common]

class InternshalaScraper:
    def __init__(self, driver_path=None, headless=False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--ignore-certificate-errors')  # Ignore SSL cert errors
        options.add_argument('--ignore-ssl-errors')
        if driver_path:
            self.driver = webdriver.Chrome(service=Service(driver_path), options=options)
        else:
            # Uses webdriver_manager to handle ChromeDriver automatically
            from webdriver_manager.chrome import ChromeDriverManager
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.maximize_window()
        self.wait = wait(self.driver, 10)
        self.action_chain = ActionChains(self.driver)

    def login(self, username: str, password: str):
        self.driver.get("https://internshala.com/")
        # Click the login button that opens the modal
        self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "login-cta"))).click()

        # Wait for the modal email input to be visible
        self.wait.until(EC.visibility_of_element_located((By.ID, "modal_email")))
        self.driver.find_element(By.ID, "modal_email").send_keys(username)
        self.driver.find_element(By.ID, "modal_password").send_keys(password)
        time.sleep(2)
        self.driver.find_element(By.ID, "modal_login_submit").click()

        # Give some time for login to process
        time.sleep(2)

    def apply_filters(self):
        # Hover over internships menu (if needed)
        try:
            internships_menu = self.wait.until(EC.presence_of_element_located((By.ID, 'internships_new_superscript')))
            self.action_chain.move_to_element(internships_menu).perform()
            time.sleep(2)
        except TimeoutException:
            print("Could not locate internships menu to hover.")

        # Disable "As per my preferences" if it's ticked
        try:
            preference_checkbox = self.driver.find_element(By.ID, "as per my preferences")
            if preference_checkbox.is_selected():
                preference_checkbox.click()
                print("Unchecked 'As per my preferences'")
            time.sleep(1)
        except Exception as e:
            print("Could not find or uncheck preferences box:", e)

        # Click Location filter and choose Work from Home
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "(//span[contains(text(),'Location')])[1]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Work from Home']"))).click()
            time.sleep(1)
        except TimeoutException:
            print("Location filter or Work from Home option not found.")

        # Click Profile filter and select 'Artificial Intelligence'
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "(//span[contains(text(),'Profile')])[1]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Artificial Intelligence']"))).click()
            time.sleep(2)
            print("Applied 'Artificial Intelligence' profile filter.")
        except Exception as e:
            print("Error applying profile filter:", e)

        # Select 'Fresher' preference if available
        try:
            fresher_checkbox = self.driver.find_element(By.XPATH, '//*[@id="search_form"]/div[1]/label')
            if not fresher_checkbox.is_selected():
                fresher_checkbox.click()
            time.sleep(1)
        except Exception:
            print("Fresher filter not available or already selected.")

        # Optional: Adjust stipend slider
        try:
            stipend_slider = self.driver.find_element(By.ID, "stipend_filter")
            self.action_chain.click_and_hold(stipend_slider).move_by_offset(-60, 0).release().perform()
            time.sleep(2)
        except Exception:
            print("Stipend slider not found or couldn't move.")


    def scrape_jobs(self, keywords=None):
        if keywords is None:
            keywords = ['Java', 'Selenium', 'Software', 'Testing', 'Programming', 'Coding', 'Competitive', 'Computer Science']

        internships = []
        while True:
            self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'container-fluid individual_internship')]")))
            job_cards = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'container-fluid individual_internship')]")

            for job_card in job_cards:
                try:
                    job_role_elem = job_card.find_element(By.TAG_NAME, 'a')
                    job_role = job_role_elem.text.strip()
                    job_link = job_role_elem.get_attribute('href')
                    company_name = job_card.find_element(By.CLASS_NAME, 'company_and_premium').text.strip()
                    stipend = job_card.find_element(By.CLASS_NAME, 'stipend').text.strip()

                    if re.compile('|'.join(keywords), re.IGNORECASE).search(job_role):
                        internships.append({
                            'role': job_role,
                            'link': job_link,
                            'company': company_name,
                            'stipend': stipend
                        })
                except Exception as e:
                    print(f"Skipping a job card due to error: {e}")

            # Check if next page button is enabled
            try:
                next_button = self.driver.find_element(By.ID, "navigation-forward")
                if 'disabled' in next_button.get_attribute('class'):
                    break  # No more pages
                else:
                    next_button.click()
                    time.sleep(3)  # wait for next page to load
            except Exception:
                print("No next page button found or error clicking it.")
                break

        return internships

    import os  # Make sure this import is at the top of your script

    def save_to_csv(self, internships, filename='internships.csv'):
       
        output_dir = os.path.join("data","joblisting")
        os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist

        # Full path to the output CSV file
        output_path = os.path.join(output_dir, filename)

        df = pd.DataFrame(internships)
        df.to_csv(output_path, index=False)
        print(f"✅ Saved {len(internships)} internships to {output_path}")


    def quit(self):
        self.driver.quit()

def run_list_scraper():
    USERNAME = "ajithaarvinth26@gmail.com"
    PASSWORD = "Aji2611#"

    scraper = InternshalaScraper(headless=False)
    try:
        scraper.login(USERNAME, PASSWORD)
        scraper.apply_filters()
        resume_path = os.path.join("data", "resume.md")
        dynamic_keywords = extract_keywords_from_resume(resume_path)

        print("📌 Extracted keywords from resume:", dynamic_keywords)

        jobs = scraper.scrape_jobs(keywords=dynamic_keywords)

        scraper.save_to_csv(jobs)
    finally:
        scraper.quit()
