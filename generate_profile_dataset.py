# ----------------------------------------------------
# File: generate_profile_dataset.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
# ----------------------------------------------------
import json
import os
import torch
import random
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# --- Configuration ---
MODEL_ID = "microsoft/phi-3-mini-4k-instruct"
# Start with a smaller number for testing, then increase (e.g., 1000+)
NUM_PROFILES_TO_GENERATE = 200
# Generate a few passwords per profile for variety
PASSWORDS_PER_PROFILE = 10
OUTPUT_FILE = "password_training_dataset.jsonl"

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
    """Loads the specified Hugging Face model and tokenizer with quantization."""
    print(f"[*] Loading AI model: {MODEL_ID}...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, quantization_config=bnb_config, trust_remote_code=True, attn_implementation="eager"
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print("[+] AI model and tokenizer loaded successfully.")
    return model, tokenizer


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


def ai_password_generator(profile, model, tokenizer, num_passwords):
    """Generates password candidates using the loaded Phi-3 model."""
    prompt = f"""<|user|>
Based on the following JSON profile, generate a list of {num_passwords} likely passwords. The passwords should be creative variations combining the profile data. Output each password on a new line, and nothing else.
Profile: {json.dumps(profile)}<|end|>
<|assistant|>
"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs, max_new_tokens=150, num_return_sequences=1, do_sample=True,
        temperature=0.8, top_p=0.9, eos_token_id=tokenizer.eos_token_id, use_cache=False
    )
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    assistant_response = generated_text.split("<|assistant|>")[-1].strip()
    return [line.strip() for line in assistant_response.split('\n') if line.strip()]


if __name__ == "__main__":
    print("--- Dataset Generation Script ---")
    if not torch.cuda.is_available():
        print("[!] WARNING: No CUDA-enabled GPU found. This script will be extremely slow.")
        exit()

    model, tokenizer = load_language_model()
    profiles = generate_synthetic_profiles(NUM_PROFILES_TO_GENERATE)

    print(f"[*] Generating password data and writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        for i, profile in enumerate(profiles):
            try:
                passwords = ai_password_generator(profile, model, tokenizer, PASSWORDS_PER_PROFILE)

                # For each generated password, create a training example
                for password in passwords:
                    # This is the format the fine-tuner will learn from.
                    # It learns to associate the input text with the desired output text.
                    training_example = {
                        "text": f"<|user|>\nBased on the following JSON profile, generate a single likely password.\nProfile: {json.dumps(profile)}<|end|>\n<|assistant|>\n{password}<|end|>"
                    }
                    f.write(json.dumps(training_example) + '\n')

                if (i + 1) % 10 == 0:
                    print(f"  ...processed {i + 1}/{len(profiles)} profiles.")
            except Exception as e:
                print(f"[!] An error occurred while processing profile {i}: {profile}")
                print(f"[!] Error: {e}")
                continue  # Skip to the next profile if an error occurs

    print(f"[+] Dataset successfully created at '{OUTPUT_FILE}'.")
