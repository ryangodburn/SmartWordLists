#-------------------------------------------
# File: MergeModel.py
# Author: Braeden Allen
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
#-------------------------------------------

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os

# --- Configuration ---
# Path to the base model on Hugging Face
base_model_id = "microsoft/phi-3-mini-4k-instruct"
# Path to your fine-tuned adapter model
adapter_path = "./phi3-password-model-final"
# Path to save the new, fully merged model
merged_model_path = "./phi3-password-model-merged"

# --- Load Base Model and Tokenizer ---
print(f"Loading base model: {base_model_id}")
# For merging, we load the model in its native float16 precision, not 4-bit
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype=torch.float16,
    trust_remote_code=True,
    device_map="cpu", # Load on CPU to avoid VRAM issues during merge
)

tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)

# --- Load the PEFT Adapter ---
print(f"Loading LoRA adapter from: {adapter_path}")
# Load the PeftModel which layers the adapter over the base model
model = PeftModel.from_pretrained(base_model, adapter_path)

# --- Merge and Save ---
print("Merging adapter weights into the base model...")
# This combines the adapter weights with the base model weights
model = model.merge_and_unload()
print("Merge complete.")

# --- Save the Final, Merged Model ---
print(f"Saving the fully merged model to: {merged_model_path}")
model.save_pretrained(merged_model_path)
tokenizer.save_pretrained(merged_model_path)

# Create a success file to indicate completion
with open(os.path.join(merged_model_path, "_MERGE_COMPLETE"), "w") as f:
    f.write("Merge successful.")

print("\nProcess complete. You can now use the model located in the")
print(f"'{merged_model_path}' directory with the updated inference script.")

