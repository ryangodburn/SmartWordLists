#-------------------------------------------
# File: XScraper.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
#-------------------------------------------

import sys
import json
import XScraper

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No username or URL provided"}))
        sys.exit(1)

    input_str = sys.argv[1]
    result = XScraper.scrape(input_str)
    print(json.dumps(result))