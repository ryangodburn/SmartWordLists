#-------------------------------------------
# File: OsintSearch.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
#-------------------------------------------

from googlesearch import search
import subprocess
import json
import re
from urllib.parse import urlparse

from GitScraper import GitScraper
from IGScraper import InstagramScraper
from LinkedInScraper import LinkedInScraper
from TTScraper import TikTokScraper

#Run X scraper in python3.11
def run_x_scraper(url):
    try:
        result = subprocess.run(
            [".venv311/bin/python3.11", "XScraperRunner.py", url],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print("X scraper failed:", e.stderr)
        return {"error": "Failed to run X scraper"}

def extract_instagram_handles(bio_text):
    return re.findall(r'@([a-zA-Z0-9._]+)', bio_text or "")

def extract_instagram_username(url):
    try:
        path = urlparse(url).path.strip("/")
        return path.split("/")[0]
    except Exception:
        return ""

visited_terms = set()  # To avoid infinite recursion

def run_osint_search(term, profile_data, depth=0, max_depth=1):
    if term in visited_terms or depth > max_depth:
        return
    visited_terms.add(term)

    from googlesearch import search
    print(f"Searching for: {term}")
    searchResult = search(term, num_results=20)

    for url in searchResult:
        if "linkedin.com/in/" in url:

            print("Found LinkedIn Material:")
            print(url)
            username = url.rstrip("/").split("/")[-1] # Strip the username
            scraper = LinkedInScraper(username)
            data = scraper.scrape_profile()
            profile_data["sources"]["LinkedIn"] = {"url": url, **data}

        elif "twitter.com/" in url or "x.com/" in url:

            print("Found Twitter Material:")
            print(url)
            data = run_x_scraper(url)
            profile_data["sources"]["Twitter"] = {"url": url, **data}

        elif "github.com/" in url: # Scrape github for information

            print("Found GitHub Material:")
            print(url)
            data = GitScraper.get_profile_info(url)
            profile_data["sources"]["GitHub"] = {"url": url, **data}

        elif "tiktok.com/@" in url:

            print("Found TikTok Material:")
            print(url)
            data = TikTokScraper.scrape_profile(url)
            profile_data["sources"]["TikTok"] = {"url": url, **data}

        elif "instagram.com/" in url:

            print("Found Instagram Material:")
            print(url)

            try:
                if "/p/" in url:  # Skip post links
                    print("Skipped Instagram post.")
                    continue
                username = extract_instagram_username(url) # Use IG URL format to get the username
                scraper = InstagramScraper(username)
                data = scraper.get_basic_info()
                profile_data["sources"]["Instagram"] = {"url": url, **data}

                tied_handles = extract_instagram_handles(data.get("Bio", ""))
                if tied_handles:
                    profile_data["sources"]["Instagram_tied"] = {}
                    for handle in tied_handles:
                        print(f"[+] Found tied Instagram handle: @{handle}")
                        tied_scraper = InstagramScraper(handle)
                        tied_data = tied_scraper.get_basic_info()
                        tied_url = f"https://www.instagram.com/{handle}/"
                        profile_data["sources"]["Instagram_tied"][handle] = {"url": tied_url, **tied_data}

                        raw_name = tied_data.get("Full Name", "").strip() # Attempts to get the name
                        next_term = handle if not raw_name or raw_name == "N/A" else raw_name
                        next_term = next_term.strip().lstrip("@")  # add this
                        if next_term and next_term not in visited_terms:
                            visited_terms.add(next_term)
                            print(f"Recursively running OSINT on tied IG account: {next_term}")
                            run_osint_search(next_term, profile_data, depth=depth + 1, max_depth=max_depth)

            except Exception as e:
                print(f"Instagram scraping failed: {e}")
        else:
            print("Other Result:")
            print(url)

        print("-------------------------------------------")

if __name__ == "__main__":

    terms = input("Enter Search Terms: ")  # For now, Boolean Searches need to be used
    profile_data = {"search_terms": terms,"sources": {}}

    run_osint_search(terms, profile_data)

    #save to JSON
    with open("profile_data.json", "w") as f:
        json.dump(profile_data, f, indent=4)

    print("Done")