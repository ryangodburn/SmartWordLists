#-------------------------------------------
# File: TTScraper.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
# Note: This is used solely for scraping my own profile, and adheres to TikTok policy
#-------------------------------------------

from playwright.sync_api import sync_playwright

class TikTokScraper:
    def __init__(self, username):
        self.username = username.lstrip('@')
        self.url = f"https://www.tiktok.com/@{self.username}"

    def scrape_profile(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(self.url, timeout=60000)

            page.wait_for_timeout(5000)  # let JS render

            try:
                name = page.query_selector("h2[data-e2e='user-title']").inner_text()
            except:
                name = "N/A"

            try:
                bio = page.query_selector("h2[data-e2e='user-bio']").inner_text()
            except:
                bio = "N/A"

            stats = {}
            try:
                count_elements = page.query_selector_all("strong[data-e2e]")
                labels = ["followers", "following", "likes"]
                for i, elem in enumerate(count_elements[:3]):
                    stats[labels[i]] = elem.inner_text()
            except:
                stats = {"followers": "N/A", "following": "N/A", "likes": "N/A"}

            browser.close()

            return {
                "name": name,
                "bio": bio,
                "stats": stats
            }