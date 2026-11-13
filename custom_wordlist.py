#-------------------------------------------
# File: custom_wordlist.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
#-------------------------------------------

import json
from itertools import product, permutations
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import datetime

# --- Configuration ---
PROFILE_FILE = "profile_data.json"
OUTPUT_FILE = "custom_wordlist.txt"
MODEL_ID = "microsoft/phi-3-mini-4k-instruct"
# Configuration for password filtering
MIN_PASSWORD_LENGTH = 8
SPECIAL_CHARACTERS = "!@#$*?_."

# === 1. Load Profile Data ===
print(f"[+] Loading profile from {PROFILE_FILE}...")
try:
    with open(PROFILE_FILE, "r") as f:
        profile = json.load(f)
except FileNotFoundError:
    print(f"[!] Error: {PROFILE_FILE} not found. Please run your OSINT script first.")
    exit()

# === 2. Load LLM for Keyword Expansion ===
print(f"[+] Loading LLM: {MODEL_ID}...")

# Use BitsAndBytesConfig for modern, stable quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load the model on the CPU first to avoid the device_map bug.
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,  # Use the config object
    trust_remote_code=True,
    attn_implementation="eager"
)

# Manually move the model to the GPU after loading.
print("[+] Moving model to GPU...")
model.to("cuda")
print("[+] Model successfully loaded on GPU.")


# === 3. Extract Keywords (Base + LLM Expanded) ===
def get_base_keywords(profile):
    """
    Extracts all single words and short phrases directly from the profile's VALUES.
    """
    keywords = set()

    def find_strings(data):
        if isinstance(data, dict):
            for v in data.values():
                find_strings(v)
        elif isinstance(data, list):
            for item in data:
                find_strings(item)
        elif isinstance(data, str) and data.strip() and data.strip() != "N/A":
            words = re.findall(r'\b[a-zA-Z0-9]+\b', data.lower())
            for word in words:
                if len(word) > 2:
                    keywords.add(word)

    find_strings(profile)
    return list(keywords)


def expand_keywords_with_llm(profile, base_keywords):
    """
    **IMPROVED**: Uses a persona-driven prompt to have the LLM brainstorm
    synonyms, related concepts, and inferred interests.
    """
    print("[+] Using LLM to expand keywords with advanced reasoning...")

    # This new prompt is much more sophisticated. It gives the AI a role and examples.
    prompt = f"""You are a creative security researcher analyzing a user's profile to guess potential password keywords.

**User Profile:**
{json.dumps(profile, indent=2)}

**Initial Keywords Found:**
{', '.join(base_keywords[:25])}

**Your Task:**
Based on the profile and keywords, brainstorm 50 additional words, concepts, synonyms, and related hobbies. Think outside the box. For example, if you see 'pentesting' or 'SQL', think about related terms like 'hacker', 'database', 'security', 'exploit', 'admin'. If you see 'travel', think of 'adventure', 'explore', 'wanderlust'.

**Output Format:**
Provide a single, comma-separated list of single words. Do not use dashes, numbers, or any other formatting.

**Brainstormed Keywords:**
"""

    model.eval()
    inputs = tokenizer(prompt, return_tensors="pt", return_attention_mask=True).to("cuda")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            use_cache=False,
            max_new_tokens=200,  # Increased tokens for a longer list
            do_sample=True,
            temperature=0.8,  # Slightly higher temp for more creativity
            repetition_penalty=1.2,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    llm_keywords = set()
    # Extract the part of the response after the final instruction.
    try:
        generated_text_part = response.split("Brainstormed Keywords:")[1].strip()
    except IndexError:
        print("[!] Warning: LLM did not follow output format. Parsing raw response.")
        generated_text_part = response

    # Split by comma and clean up each potential keyword
    words = generated_text_part.split(',')
    for word in words:
        cleaned_word = re.sub(r'[^a-zA-Z0-9]', '', word).lower().strip()
        if len(cleaned_word) > 2 and cleaned_word not in base_keywords:
            llm_keywords.add(cleaned_word)

    print(f"[+] LLM generated {len(llm_keywords)} new keywords.")
    return list(llm_keywords)


# --- Main Keyword Generation ---
base_keywords = get_base_keywords(profile)
llm_keywords = expand_keywords_with_llm(profile, base_keywords)
all_keywords = sorted(list(set(base_keywords + llm_keywords)))
print(f"[+] Total unique keywords: {len(all_keywords)}")

# === 4. Generate Password Variants (The "Beefed Up" Part) ===
print("[+] Generating password mutations...")
mutated_passwords = set()

# --- Define Mutation Components ---
current_year = datetime.datetime.now().year
grad_year_str = ""
# Safely get graduation year
if 'sources' in profile and 'LinkedIn' in profile['sources'] and 'grad_year' in profile['sources']['LinkedIn']:
    grad_year_str = str(profile['sources']['LinkedIn']['grad_year'])

years = {str(current_year), str(current_year + 1), "2024", "2025"}
if grad_year_str:
    years.add(grad_year_str)
    if len(grad_year_str) == 4:
        years.add(grad_year_str[-2:])  # e.g., "25"

common_numbers = {"1", "123", "1234", "12345", "7", "3", "0", "99", "10"}
symbols = set(SPECIAL_CHARACTERS)
affixes = set(years) | common_numbers | symbols
affixes.add("")  # Include mutations with no affix

leetspeak_map = {'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '$', 't': '7', 'l': '1'}


# --- Define Mutation Functions ---
def apply_leetspeak(word):
    """Applies common leetspeak substitutions."""
    for char, sub in leetspeak_map.items():
        word = word.replace(char, sub)
    return word


# --- Apply Mutations ---

# Rule 1: Single keyword mutations
for word in all_keywords:
    if not word.isalnum() or len(word) < 3 or len(word) > 12:
        continue

    word_variations = {
        word,
        word.capitalize(),
        word.upper(),
        apply_leetspeak(word)
    }

    for variation, affix in product(word_variations, affixes):
        mutated_passwords.add(f"{variation}{affix}")
        if affix:
            mutated_passwords.add(f"{affix}{variation}")

# Rule 2: Two-keyword combinations
# Use permutations to get both (word1, word2) and (word2, word1)
# Limit to first 50 keywords to keep combinations manageable but effective
for word1, word2 in permutations(all_keywords[:50], 2):
    if not (word1.isalnum() and word2.isalnum()):
        continue
    if len(word1) + len(word2) > 16: continue

    mutated_passwords.add(f"{word1}{word2}")
    mutated_passwords.add(f"{word1.capitalize()}{word2.capitalize()}")

    for affix in (years | symbols):
        if affix:
            mutated_passwords.add(f"{word1}{affix}{word2}")


# === 5. Filter Passwords ===
def filter_passwords(passwords, min_length, special_chars):
    """Filter a list of passwords based on complexity rules."""
    print(f"[+] Filtering {len(passwords)} passwords...")

    strong_passwords = []
    for pwd in passwords:
        # Rule 1: Check length
        if len(pwd) < min_length:
            continue

        # Rule 2: Check for at least one number
        if not any(char.isdigit() for char in pwd):
            continue

        # Rule 3: Check for at least one special character
        if not any(char in special_chars for char in pwd):
            continue

        strong_passwords.append(pwd)

    print(f"[+] Found {len(strong_passwords)} passwords that meet the criteria.")
    return strong_passwords


# === 6. Save to File ===
# First, filter the generated list
filtered_list = filter_passwords(mutated_passwords, MIN_PASSWORD_LENGTH, SPECIAL_CHARACTERS)

print(f"[+] Writing {len(filtered_list)} filtered passwords to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, "w") as f:
    f.write("\n".join(sorted(filtered_list)))

print("[+] Done!")