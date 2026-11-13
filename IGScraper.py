#-------------------------------------------
# File: IGScraper.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
#-------------------------------------------

import instaloader
import re
from urllib.parse import urlparse

class InstagramScraper:

    def extract_username_from_url(url):
        # Strips an Instagram URL down to just the username
        try:
            parsed = urlparse(url)
            path = parsed.path.strip("/")
            return path.split("/")[0] if path else None
        except Exception as e:
            print(f"[!] Failed to extract Instagram username from URL: {e}")
            return None


    def __init__(self, username_or_url):
        if "instagram.com" in username_or_url:
            username = self.extract_username_from_url(username_or_url)
        else:
            username = username_or_url

        self.username = username
        self.loader = instaloader.Instaloader()
        self.profile = None

    def load_profile(self):
        try:
            self.profile = instaloader.Profile.from_username(self.loader.context, self.username)
            print(f"[✓] Profile loaded: {self.profile.full_name}")
        except Exception as e:
            print(f"[!] Error loading profile for '{self.username}': {e}")

    # def get_posts_info(self, max_posts=10): # Unused due to security on Instagram
    #     if not self.profile:
    #         self.load_profile()
    #     if not self.profile:
    #         return []
    #
    #     posts_data = []
    #     try:
    #         for idx, post in enumerate(self.profile.get_posts()):
    #             if idx >= max_posts:
    #                 break
    #             posts_data.append({
    #                 "Caption": post.caption,
    #                 "Location": post.location.name if post.location else None,
    #                 "Timestamp": post.date_utc.isoformat(),
    #                 "Likes": post.likes,
    #                 "Hashtags": post.caption_hashtags,
    #                 "URL": f"https://www.instagram.com/p/{post.shortcode}/"
    #             })
    #     except Exception as e:
    #         print(f"[!] Error fetching posts: {e}")
    #     return posts_data

    def get_basic_info(self):
        if not self.profile:
            self.load_profile()
        if not self.profile:
            return {"Error": "Unable to load profile."}

        try:
            return {
                "Full Name": self.profile.full_name or "N/A",
                "Username": self.profile.username,
                "Bio": self.profile.biography or "N/A",
                "Is Private": self.profile.is_private,
                "Followers": self.profile.followers,
                "Following": self.profile.followees,
                "Posts": self.profile.mediacount,
                "External URL": self.profile.external_url or "N/A",
            }
        except Exception as e:
            print(f"[!] Error getting basic info: {e}")
            return {"Error": str(e)}

    def download_profile_pic(self):
        self.loader.download_profile(self.username, profile_pic_only=True) # Can download a pp if desired