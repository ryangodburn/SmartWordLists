#-------------------------------------------
# File: XScraper.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
#-------------------------------------------

import snscrape.modules.twitter as Twitter

class Xscraper:
    def __init__(self, username):
        self.username = username.lstrip('@')

    def get_profile_info(self):
        try:
            user = Twitter.TwitterUserScraper(self.username).entity
            return {
                "name": user.display_name,
                "username": user.username,
                "location": user.location,
                "followers": user.followers,
                "following": user.following,
                "tweets": user.tweets
            }
        except Exception as e:
            return {"error": str(e)}

    def get_recent_posts(self, count=5):
        posts = []
        try:
            for i, tweet in enumerate(Twitter.TwitterUserScraper(self.username).get_items()):
                if i >= count:
                    break
                posts.append({"date": str(tweet.date.date()), "text": tweet.text})
        except Exception as e:
            posts.append({"error": str(e)})
        return posts


def scrape(url_or_username):
    import re
    match = re.search(r"(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)", url_or_username)
    username = match.group(1) if match else url_or_username
    scraper = Xscraper(username)
    profile = scraper.get_profile_info()
    posts = scraper.get_recent_posts(3)
    return {
        "profile": profile,
        "recent_posts": posts
    }
