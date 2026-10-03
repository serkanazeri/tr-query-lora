"""Run base and LoRA on the held-out synthetic test split and compare executed results."""

import argparse
import json
import sqlite3
import time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from common import MODEL_ID, compile_plan, parse_plan, question_prompt

ROOT = Path(__file__).resolve().parents[1]


def run_query(connection, plan):
    sql, binds = compile_plan(plan)
    return [tuple(row) for row in connection.execute(sql, binds).fetchall()]


def generate(model, tokenizer, question, device):
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": question_prompt(question)}],
        tokenize=True, add_generation_prompt=True, return_tensors="pt",
    ).to(device)
    started = time.monotonic()
    with torch.inference_mode():
        output = model.generate(
            prompt,
            attention_mask=torch.ones_like(prompt),
            max_new_tokens=120,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=[tokenizer.eos_token_id, tokenizer.convert_tokens_to_ids('<end_of_turn>')],
        )
    raw = tokenizer.decode(output[0][prompt.shape[-1]:], skip_special_tokens=True).strip()
    return raw, round((time.monotonic() - started) * 1000)


def evaluate_model(model, tokenizer, rows, connection, device):
    details = []
    for row in rows:
        raw, latency_ms = generate(model, tokenizer, row["question"], device)
        try:
            plan = parse_plan(raw)
            valid = True
            exact = plan == row["plan"]
            execution_equal = run_query(connection, plan) == run_query(connection, row["plan"])
            failure = None
        except (ValueError, json.JSONDecodeError) as error:
            plan, valid, exact, execution_equal, failure = None, False, False, False, str(error)
        details.append({
            "question": row["question"], "expected": row["plan"], "raw": raw, "parsed": plan,
            "valid_json_plan": valid, "exact_plan": exact, "execution_equal": execution_equal,
            "latency_ms": latency_ms, "failure": failure,
        })
    n = len(details)
    return {
        "count": n,
        "valid_plan_rate": sum(x["valid_json_plan"] for x in details) / n,
        "exact_plan_rate": sum(x["exact_plan"] for x in details) / n,
        "execution_accuracy": sum(x["execution_equal"] for x in details) / n,
        "latency_p50_ms": sorted(x["latency_ms"] for x in details)[n // 2],
        "details": details,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--adapter", type=Path, default=ROOT / "artifacts" / "lora")
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "test.jsonl")
    parser.add_argument("--limit", type=int, default=96)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "evaluation.json")
    args = parser.parse_args()
    if not args.adapter.joinpath("adapter_model.safetensors").exists():
        raise SystemExit("Adapter bulunamadı; önce training/train.py çalıştırın.")
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    base = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float16 if device != "cpu" else torch.float32).to(device)
    base.eval()
    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines()][:args.limit]
    connection = sqlite3.connect(":memory:")
    connection.executescript((ROOT / "migrations" / "0001_init.sql").read_text(encoding="utf-8"))
    base_result = evaluate_model(base, tokenizer, rows, connection, device)
    tuned = PeftModel.from_pretrained(base, args.adapter)
    tuned.eval()
    tuned_result = evaluate_model(tuned, tokenizer, rows, connection, device)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "base_model": args.model, "adapter": str(args.adapter), "test_split": str(args.dataset),
        "synthetic_data": True, "base": base_result, "lora": tuned_result,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"base": {k: v for k, v in base_result.items() if k != "details"},
                      "lora": {k: v for k, v in tuned_result.items() if k != "details"}}, indent=2))


if __name__ == "__main__":
    main()
