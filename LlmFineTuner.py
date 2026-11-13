# ----------------------------------------------------
# File: LlmFineTuner.py
# Author: Braeden
# Advisor: Murat Gunestas
# Project: SmarterWordlists
# Copyright 2025
# ----------------------------------------------------

import torch
import argparse
import math
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig
from trl import SFTTrainer

def main(args):
    """
    The main function to run the fine-tuning process.
    """
    # --- Configuration ---
    BASE_MODEL_ID = "microsoft/phi-3-mini-4k-instruct"
    DATASET_FILE = args.dataset_file
    OUTPUT_MODEL_DIR = args.output_dir

    # 1. Load the Dataset and Split It
    print(f"[*] Loading dataset from {DATASET_FILE}...")
    # Load the full dataset
    full_dataset = load_dataset("json", data_files=DATASET_FILE, split="train")

    dataset_split = full_dataset.train_test_split(test_size=0.1, shuffle=True, seed=42)
    train_dataset = dataset_split["train"]
    eval_dataset = dataset_split["test"]
    print(
        f"[+] Dataset loaded and split: {len(train_dataset)} training samples, {len(eval_dataset)} evaluation samples.")

    # 2. Load the Model and Tokenizer
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    print(f"[*] Loading base model: {BASE_MODEL_ID}...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        trust_remote_code=True,
        attn_implementation="eager"
    )
    model.config.use_cache = False

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    print("[+] Model and tokenizer loaded.")

    # 3. Configure LoRA
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        # Using the more comprehensive target modules for Phi-3
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )

    # 4. Set Training Arguments
    # Incorporating evaluation and saving strategy from your script
    per_device_batch_size = 4
    gradient_accumulation_steps = 4

    # Calculate steps per epoch to save/eval at the end of each epoch
    steps_per_epoch = math.ceil(len(train_dataset) / (per_device_batch_size * gradient_accumulation_steps))

    training_args = TrainingArguments(
        output_dir=f"./{OUTPUT_MODEL_DIR}-checkpoint",
        per_device_train_batch_size=per_device_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=2e-4,
        logging_steps=10,
        num_train_epochs=args.num_epochs,  # Use epochs from arguments
        # Evaluation arguments
        do_eval=True,
        evaluation_strategy="steps",
        eval_steps=steps_per_epoch,  # Evaluate at the end of each epoch
        # Saving arguments
        save_strategy="steps",
        save_steps=steps_per_epoch,  # Save a checkpoint at the end of each epoch
        save_total_limit=3,  # Keep only the last 3 checkpoints
        fp16=True,
        report_to="none",
    )

    # 5. Initialize the Trainer
    # SFTTrainer will handle the formatting and tokenization automatically
    # because our dataset has the correct "text" field.
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,  # Add the evaluation dataset
        peft_config=lora_config,
        dataset_text_field="text",
        tokenizer=tokenizer,
        args=training_args,
        max_seq_length=512,
    )

    # 6. Start Fine-Tuning
    print(f"[*] Starting model training for {args.num_epochs} epochs...")
    trainer.train()
    print("[+] Fine-tuning complete.")

    # 7. Save the Final Model
    print(f"[*] Saving final model to {OUTPUT_MODEL_DIR}...")
    trainer.save_model(OUTPUT_MODEL_DIR)
    tokenizer.save_pretrained(OUTPUT_MODEL_DIR)
    print(f"[+] Model saved successfully to {OUTPUT_MODEL_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reusable fine-tuning script for Phi-3 models.")
    parser.add_argument("--dataset_file", type=str, required=True, help="Path to the .jsonl training dataset.")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save the final fine-tuned model.")
    parser.add_argument("--num_epochs", type=int, default=3, help="Number of training epochs to perform.")

    args = parser.parse_args()
    main(args)