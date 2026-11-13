# ----------------------------------------------------
# File: testPasswordCreation.py
# Author: Braeden
# Advisor: Murat Gunestas
# Project: SmarterWordlists - Validation Part
# Copyright 2025
# ----------------------------------------------------
import hashlib
import random
import json
import os
import torch
import requests  # New import for making API requests
import time  # New import for rate limiting
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# --- AI Model Configuration ---
MODEL_ID = "./phi3-password-model-merged"

# --- Script Configuration ---
NUM_PROFILES_TO_GENERATE = 1000
PASSWORDS_PER_PROFILE = 20

# --- Data for Synthetic Profile Generation ---
COMMON_FIRST_NAMES = [
    "jessica", "michael", "ashley", "christopher", "emily", "matthew",
    "samantha", "joshua", "sarah", "tyler", "taylor", "brandon", "brittany",
    "jacob", "amanda", "daniel", "elizabeth", "nicholas", "megan", "andrew",
    "nicole", "joseph", "kayla", "zachary", "rachel", "david", "lauren",
    "james", "stephanie", "john", "hannah", "ryan", "jennifer", "austin",
    "alexis", "anthony", "victoria", "william", "danielle", "justin", "amber",
    "robert", "courtney", "alexander", "jasmine", "jonathan", "rebecca",
    "kyle", "morgan", "cody", "alyssa", "kevin", "brianna", "thomas",
    "alexandra", "aaron", "kelsey", "jordan", "katherine", "eric", "melissa",
    "benjamin", "kimberly", "dylan", "michelle", "samuel", "allison",
    "steven", "tiffany", "christian", "haley", "jose", "mary", "brian",
    "chelsea", "adam", "christina", "timothy", "shelby", "nathan", "anna",
    "richard", "abigail", "patrick", "sara", "charles", "heather", "sean",
    "erin", "jesse", "laura", "jason", "maria", "jeremy", "kaitlyn", "mark",
    "andrea", "stephen", "olivia", "alex"
]
COMMON_LAST_NAMES = [
    "smith", "johnson", "williams", "jones", "brown", "davis", "miller",
    "wilson", "moore", "taylor", "anderson", "thomas", "jackson", "white",
    "harris", "martin", "thompson", "garcia", "martinez", "robinson",
    "clark", "rodriguez", "lewis", "lee", "walker", "hall", "allen", "young",
    "hernandez", "king", "wright", "lopez", "hill", "scott", "green",
    "adams", "baker", "gonzalez", "nelson", "carter", "mitchell", "perez",
    "roberts", "turner", "phillips", "campbell", "parker", "evans",
    "edwards", "collins"
]
COMMON_CITIES = [
    "newyorkcity", "losangeles", "chicago", "houston", "phoenix",
    "sanantonio", "philadelphia", "sandiego", "dallas", "fortworth",
    "jacksonville", "austin", "sanjose", "charlotte", "columbus",
    "indianapolis", "sanfrancisco", "seattle", "oklahomacity", "denver",
    "nashville", "washington", "elpaso", "lasvegas", "boston", "detroit",
    "louisville", "portland", "memphis", "albuquerque", "baltimore",
    "milwaukee", "tucson", "fresno", "sacramento", "atlanta", "mesa",
    "kansascity", "coloradosprings", "raleigh", "omaha", "miami",
    "virginiabeach", "longbeach", "oakland", "minneapolis", "bakersfield",
    "tampa", "tulsa", "arlington"
]
COMMON_INTERESTS = [
    "reading", "martialarts", "jewelrymaking", "woodworking", "gardening",
    "videogames", "fishing", "teamsports", "walking", "yoga", "traveling",
    "golf", "watchingsports", "playingcards", "boardgames", "eatingout",
    "writing", "running", "tennis", "volunteerwork", "dancing", "painting",
    "cooking", "bicycling", "housework", "moviewatching", "genealogy",
    "churchactivities", "calligraphy", "podcasts", "television", "collecting",
    "music", "skiing", "snowboarding", "shopping", "socializing", "quilting"
]


def load_language_model():
    """
    Loads the specified Hugging Face model and tokenizer with quantization.
    This should be called once at the start of the script.
    Requires a CUDA-enabled GPU.
    """
    print(f"[*] Loading AI model: {MODEL_ID}...")

    # Use 4-bit quantization to load the model efficiently on consumer GPUs
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    # Load the model from Hugging Face
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        trust_remote_code=True,
        attn_implementation="eager"
    )

    # Load the tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    # Set padding token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("[+] AI model and tokenizer loaded successfully.")
    return model, tokenizer


def ai_password_generator(profile, model, tokenizer, num_passwords):
    """Generates password candidates using the loaded Phi-3 model."""
    prompt = f"""<|user|>
Based on the following JSON profile, generate a list of {num_passwords} likely passwords. The passwords should be creative variations combining the profile data. Output each password on a new line, and nothing else.
Profile: {json.dumps(profile)}<|end|>
<|assistant|>
"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        num_return_sequences=1,
        do_sample=True,
        temperature=0.8,
        top_p=0.9,
        eos_token_id=tokenizer.eos_token_id,
        use_cache=False
    )
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    assistant_response = generated_text.split("<|assistant|>")[-1].strip()
    candidates = [line.strip() for line in assistant_response.split('\n') if line.strip()]
    return candidates


def generate_synthetic_profiles(num_profiles):
    """Generates a list of plausible, random, synthetic user profiles."""
    print(f"[*] Generating {num_profiles} synthetic profiles...")
    profiles = []
    for _ in range(num_profiles):
        profile = {
            "name": f"{random.choice(COMMON_FIRST_NAMES)}{random.choice(COMMON_LAST_NAMES)}",
            "birth_year": str(random.randint(1970, 2010)),
            "location": random.choice(COMMON_CITIES),
            "interest": random.choice(COMMON_INTERESTS)
        }
        profiles.append(profile)
    print(f"[+] {len(profiles)} profiles generated.")
    return profiles


def check_password_with_hibp(password):
    """
    Checks a single password against the HIBP Pwned Passwords API
    using the k-Anonymity model.

    Args:
        password (str): The plaintext password to check.

    Returns:
        bool: True if the password was found in a breach, False otherwise.
    """
    # 1. Hash the password with SHA-1
    sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()

    # 2. Split the hash into a prefix (first 5 chars) and a suffix (the rest)
    prefix, suffix = sha1_hash[:5], sha1_hash[5:]

    # 3. Query the HIBP API with the prefix
    api_url = f'https://api.pwnedpasswords.com/range/{prefix}'
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            print(f"[!] Warning: HIBP API returned status {response.status_code}")
            return False

        # 4. Check if our suffix is in the response list
        # The response is a list of suffixes, each on a new line.
        found_hashes = (line.split(':')[0] for line in response.text.splitlines())
        if suffix in found_hashes:
            return True

    except requests.exceptions.RequestException as e:
        print(f"[!] Error querying HIBP API: {e}")
        # Wait a moment before trying again later
        time.sleep(5)
        return False

    return False


def validate_passwords(profiles, model, tokenizer):
    """The main validation loop using the HIBP API."""
    print("\n[*] Starting validation process using HIBP API...")
    total_passwords_generated = 0
    discovered_passwords = []

    for i, profile in enumerate(profiles):
        password_candidates = ai_password_generator(profile, model, tokenizer, PASSWORDS_PER_PROFILE)
        total_passwords_generated += len(password_candidates)

        for password in password_candidates:
            # Check each password against the API
            if check_password_with_hibp(password):
                print(f"\n--- DISCOVERY! ---")
                print(f"  [+] Found Match in HIBP: {password}")
                print(f"  [+] From Profile: {json.dumps(profile)}")
                print("------------------\n")
                discovered_passwords.append((password, profile))

            # Add a small delay to be respectful to the API
            time.sleep(0.1)

        if (i + 1) % 10 == 0:
            print(f"  ...processed {i + 1}/{len(profiles)} profiles.")

    print("[*] Validation complete.")
    return discovered_passwords, total_passwords_generated


if __name__ == "__main__":
    print("--- AI-Powered API-Based Password Validation Script ---")

    if not torch.cuda.is_available():
        print("[!] WARNING: No CUDA-enabled GPU found. This script will be extremely slow.")

    # 1. Load the AI Model (do this once)
    model, tokenizer = load_language_model()

    # 2. Generate a set of synthetic profiles
    synthetic_profiles = generate_synthetic_profiles(NUM_PROFILES_TO_GENERATE)

    # 3. Run the validation process (no longer needs target_hashes)
    discoveries, total_generated = validate_passwords(synthetic_profiles, model, tokenizer)

    # 4. Print the final report
    print("\n--- FINAL REPORT ---")
    print(f"Total Synthetic Profiles Tested: {len(synthetic_profiles)}")
    print(f"Total Passwords Generated & Checked: {total_generated}")
    print(f"Total Passwords Found in Breaches: {len(discoveries)}")
    print("--------------------\n")

    if discoveries:
        print("Discovered Passwords:")
        for password, profile in discoveries:
            print(f"  - Password: '{password}' (from profile: {profile['name']}, {profile['birth_year']})")
