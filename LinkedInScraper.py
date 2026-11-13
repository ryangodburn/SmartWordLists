#-------------------------------------------
# File: LinkedInScraper.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
#-------------------------------------------

from playwright.sync_api import sync_playwright
import json

class LinkedInScraper:
    def __init__(self, username, cookie_file="linkedin_cookies.json"):
        self.username = username.lstrip("@")
        self.profile_url = f"https://www.linkedin.com/in/{self.username}/"
        self.experience_url = f"https://www.linkedin.com/in/{self.username}/details/experience/"
        self.cookie_file = cookie_file

    def load_cookies(self, context):
        with open(self.cookie_file, "r") as f:
            cookies = json.load(f)

        cleaned_cookies = []
        for cookie in cookies:
            if cookie["domain"].startswith("."):
                cookie["domain"] = cookie["domain"][1:]
            if cookie.get("sameSite") not in {"Lax", "Strict", "None"}:
                cookie["sameSite"] = "Lax"
            cookie.setdefault("path", "/")
            cookie.setdefault("secure", True)
            cleaned_cookies.append(cookie)

        context.add_cookies(cleaned_cookies)

    def safe_text(self, locator):
        try:
            return locator.first.text_content().strip()
        except:
            return "N/A"

    def scroll_page(self, page, scrolls=5, delay=0.8):
        for _ in range(scrolls):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(int(delay * 1000))

    def scrape_main_profile(self, page):
        page.goto(self.profile_url, timeout=15000)
        page.wait_for_timeout(3000)
        self.scroll_page(page, scrolls=7, delay=1)

        # Confirm login
        if "Sign in" in page.title():
            print("[!] Not logged in. Cookies may be expired.")
            return None

        name = self.safe_text(page.locator("h1"))
        headline = self.safe_text(page.locator("div.text-body-medium"))
        location = self.safe_text(page.locator("span.text-body-small"))

        # About/Bio
        try:
            bio_locator = page.locator('section:has-text("About") div.inline-show-more-text span[aria-hidden="true"]')
            bio = self.safe_text(bio_locator)
        except:
            bio = "N/A"

        # Scrape skills
        skills = self.scrape_skills_details(page)

        # Scrape interests
        interests = self.scrape_interests(page)

        return {
            "url": self.profile_url,
            "name": name,
            "headline": headline,
            "location": location,
            "bio": bio,
            "skills": skills,
            "interests": interests
        }

    def scrape_experience_details(self, page):
        page.goto(self.experience_url, timeout=15000)
        page.wait_for_timeout(3000)
        self.scroll_page(page, scrolls=10, delay=1)

        experience_list = []
        try:
            job_cards = page.locator('li.pvs-list__paged-list-item, li.pvs-list__item')
            count = job_cards.count()
            for i in range(min(count, 10)):
                job = job_cards.nth(i)
                title = self.safe_text(job.locator('span[aria-hidden="true"]'))
                company = self.safe_text(job.locator('span.t-normal, div.pvs-entity__secondary-title'))
                experience_list.append({"title": title, "company": company})
        except Exception as e:
            print(f"[!] Error scraping experience details: {e}")
        return experience_list

    def scrape_skills_details(self, page):
        skills_url = f"https://www.linkedin.com/in/{self.username}/details/skills/"
        page.goto(skills_url, timeout=15000)
        page.wait_for_timeout(3000)
        self.scroll_page(page, scrolls=10, delay=1)

        skills = []
        try:
            skill_items = page.locator('li.pvs-list__paged-list-item, li.pvs-list__item')
            count = skill_items.count()
            for i in range(min(count, 50)):  # Get up to 50 skills
                skill = self.safe_text(skill_items.nth(i).locator('span[aria-hidden="true"]'))
                if skill != "N/A":
                    skills.append(skill)
        except Exception as e:
            print(f"[!] Error scraping skills details: {e}")
        return skills

    def scrape_interests(self, page):
        interests = []
        try:
            # Scroll down to bottom so interests load
            self.scroll_page(page, scrolls=10, delay=1)

            # Wait for Interests section to appear (timeout 7s)
            page.wait_for_selector('section.pv-interests-section', timeout=7000)
            interest_section = page.locator('section.pv-interests-section')

            # Each interest is usually a span inside a list item
            interest_items = interest_section.locator(
                'li.pv-interests-section__list-item span.pv-entity__summary-title-text')
            count = interest_items.count()
            for i in range(count):
                interest_name = interest_items.nth(i).text_content().strip()
                if interest_name:
                    interests.append(interest_name)
        except Exception as e:
            print(f"[!] Error scraping interests: {e}")

        return interests

    def scrape_profile(self):
        with sync_playwright() as p: # For browser launch
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1280, "height": 1024})
            self.load_cookies(context)
            page = context.new_page()

            # Main profile info + bio + interests
            profile_data = self.scrape_main_profile(page)
            if profile_data is None:
                browser.close()
                return {"error": "Not logged in or failed to load main profile"}

            # Experience
            profile_data["experience"] = self.scrape_experience_details(page)

            # Skills
            profile_data["skills"] = self.scrape_skills_details(page)

            browser.close()
            return profile_data