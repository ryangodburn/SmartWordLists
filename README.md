# SmartWordlists
Leveraging AI and OSINT for targeted password attacks and list generation

# AI-Driven Targeted Password List Generator

This project explores the use of AI and OSINT to generate personalized, context-aware password lists that outperform generic wordlists like `rockyou.txt`. By combining public data collection with large language models (LLMs), this tool simulates realistic password guessing for red teaming, auditing, forensics, and research purposes.

---

## Overview

Traditional password cracking often relies on static dictionaries, but users tend to choose passwords based on personal information — names, birthdays, interests. This project automates the creation of **targeted wordlists** using:

- **OSINT profiling**: Collecting public user data from social media, forums, and usernames
- **LLM-based password generation**: Generating realistic passwords using GPT-4-style models
- **Probabilistic pattern modeling**: Optionally merging grammars and substitution rules

---

## Features

- **User Profiling** — Create user JSON profiles using scraped or synthetic data
- **AI Password Generation** — Generate passwords based on name, DOB, hobbies, etc.
- **Pattern Customization** — Include leetspeak, case variants, symbols, and grammar structures
- **Benchmarking Mode** — Compare crack rates vs. `rockyou.txt` and CUPP-generated lists

---

## Project Structure

