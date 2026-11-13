#-------------------------------------------
# File: GitScraper.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
#-------------------------------------------

import requests

class GitScraper:
    def __init__(self, username):
        self.username = username.strip()
        self.api_url = f"https://api.github.com/users/{self.username}"
        self.response = None

    def load_profile(self):
        print(f"Fetching GitHub profile for: {self.username}")
        try:
            self.response = requests.get(self.api_url)
            print("Response status code:", self.response.status_code)
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            self.response = None

    def get_profile_info(self):
        if self.response is None:
            print("No response received")
        elif self.response.status_code == 200:
            data = self.response.json()
            print("Name:", data["name"])
            print("Bio:", data["bio"])
            print("Public Repos:", data["public_repos"])
            print("Followers:", data["followers"])
        elif self.response.status_code == 404:
            print("No profile found")
        else:
            print("Error: " , self.response.status_code)