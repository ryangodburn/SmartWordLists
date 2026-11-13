import json
import re

def clean_text(text):
    # Remove non-printable/control characters
    return re.sub(r"[^\x20-\x7E]", "", text)

output_path = "rockyou_dataset.jsonl"

with open("rockyou.txt", "r", encoding="latin1") as infile, open(output_path, "w", encoding="utf-8") as outfile:
    for line in infile:
        pwd = clean_text(line.strip())

        # Filter: length, no spaces, at least one digit or special char
        if (
            6 <= len(pwd) <= 16 and
            " " not in pwd and
            re.search(r"[0-9!@#$%^&*()_+=\-]", pwd)
        ):
            prompt = "Generate a password based on real-world usage."
            json_line = {"prompt": prompt, "response": pwd}
            outfile.write(json.dumps(json_line) + "\n")

print("rockyou_dataset.jsonl created and filtered.")
