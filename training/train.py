"""Supervised LoRA training for Gemma 2B on Apple Silicon or CUDA.

Requires access to google/gemma-2b-it and a GPU. It never trains base weights.
"""

import argparse
import json
import random
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, DataCollatorForSeq2Seq, Trainer, TrainingArguments

from common import MODEL_ID, question_prompt

ROOT = Path(__file__).resolve().parents[1]


class QueryDataset(Dataset):
    def __init__(self, path: Path, tokenizer, max_length: int):
        self.rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            prompt = [{"role": "user", "content": question_prompt(row["question"])}]
            completion = {"role": "assistant", "content": json.dumps(row["plan"], ensure_ascii=False, separators=(",", ":"))}
            prefix = tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True)
            full = tokenizer.apply_chat_template(prompt + [completion], tokenize=True, add_generation_prompt=False)
            if full[:len(prefix)] != prefix:
                raise RuntimeError("Chat-template prompt prefix changed; inspect labels before training")
            if len(full) > max_length:
                raise RuntimeError(f"Example exceeds max_length={max_length}; increase it rather than silently truncate")
            self.rows.append({
                "input_ids": full,
                "attention_mask": [1] * len(full),
                "labels": [-100] * len(prefix) + full[len(prefix):],
            })

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        return self.rows[index]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "lora")
    parser.add_argument("--steps", type=int, default=240)
    parser.add_argument("--max-length", type=int, default=384)
    args = parser.parse_args()

    torch.manual_seed(20261003)
    random.seed(20261003)
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else None
    if device is None:
        raise SystemExit("GPU bulunamadı. Apple Silicon için MPS destekli PyTorch veya CUDA GPU gerekir.")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    base = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float16)
    base.config.use_cache = False
    base.to(device)
    config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(base, config)
    model.enable_input_require_grads()
    model.print_trainable_parameters()
    train_data = QueryDataset(ROOT / "data" / "train.jsonl", tokenizer, args.max_length)
    valid_data = QueryDataset(ROOT / "data" / "valid.jsonl", tokenizer, args.max_length)
    args.output.mkdir(parents=True, exist_ok=True)
    training = TrainingArguments(
        output_dir=str(args.output / "checkpoints"),
        max_steps=args.steps,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_ratio=0.05,
        weight_decay=0.01,
        logging_steps=20,
        eval_strategy="steps",
        eval_steps=80,
        save_strategy="no",
        report_to="none",
        remove_unused_columns=False,
        dataloader_pin_memory=False,
        seed=20261003,
        optim="adamw_torch",
    )
    trainer = Trainer(
        model=model,
        args=training,
        train_dataset=train_data,
        eval_dataset=valid_data,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, label_pad_token_id=-100, pad_to_multiple_of=8),
    )
    result = trainer.train()
    model.save_pretrained(args.output, safe_serialization=True)
    tokenizer.save_pretrained(args.output)
    (args.output / "training_summary.json").write_text(json.dumps({
        "base_model": args.model,
        "method": "LoRA, no 4-bit quantization",
        "device": device,
        "rank": 8,
        "alpha": 16,
        "targets": ["q_proj", "v_proj"],
        "steps": args.steps,
        "train_examples": len(train_data),
        "validation_examples": len(valid_data),
        "train_loss": result.training_loss,
        "seed": 20261003,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Adapter saved to {args.output}")


if __name__ == "__main__":
    main()
