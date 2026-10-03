# TR-Query

**A measurable LoRA experiment for Turkish analytics questions.** The app maps a question about fictional retail operations to a four-field query plan. It compares the same Gemma 2B base model before and after LoRA adaptation, then shows the validated plan, compiled read-only SQL, and result over synthetic data.

> **Live demo:** [tr-query-lora.serkanazeri.workers.dev](https://tr-query-lora.serkanazeri.workers.dev) · [GitHub repository](https://github.com/serkanazeri/tr-query-lora). A standard LoRA adapter was trained locally on an M4 Pro and uploaded to Cloudflare Workers AI. Live inference and D1 results were verified with three questions. See the [results report](docs/results.md) for measurements and observed failures.

[Türkçe](README.md) · [Architecture](docs/architecture.md) · [Evaluation](docs/evaluation.md) · [Results](docs/results.md) · [Operations](docs/operations.md)

## Measured results

| Dataset | Base model | Deployed LoRA |
| --- | ---: | ---: |
| 96 synthetic questions with held-out sentence frames, exact plan | 0/96 | 96/96 |
| 12 new audit questions excluded from training, exact plan | 0/12 | 7/12 |

All three live demo examples returned the intended plan and D1 result. The 12-question audit set is small and its labels have not been independently reviewed; 7/12 remains a material limitation. The [results report](docs/results.md) preserves both training iterations and per-question outputs.

## What this demonstrates

- A reproducible synthetic dataset with distinct training, validation, and held-out wording templates.
- Standard LoRA, not QLoRA: rank 8 on `q_proj` and `v_proj`, with unquantized base weights.
- A matched base-versus-adapter comparison using the same prompt and decoding settings.
- Strict validation of the first complete JSON plan and a fixed SQL compiler. Trailing generation is disclosed as a warning and remains available in the raw output. Model-authored SQL is never executed.
- A small public demo budget. Free-tier exhaustion produces an explicit error, not a hidden paid fallback.

The synthetic dataset has 18 order records. The fixed reference date is 2026-09-30. The test split holds out sentence templates, but repeats the same metric, grouping, period, and city combinations. It does **not** prove transfer to an unseen customer schema or real operational impact.

GitHub Actions checks plan tests, the app build, Python syntax, and deterministic dataset regeneration on every push and pull request. Gated model weights are not sent to CI; LoRA results come from the separate local evaluation.

## Run locally

```bash
npm ci
npm run build
npm run db:local
npm run preview
```

Open `http://localhost:8789`. The published LoRA adapter ID is configured. Local Wrangler AI bindings access the remote AI service and may consume the shared free quota.

```bash
python3 training/generate_data.py
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python training/train.py --steps 320 --output artifacts/lora-v2
.venv/bin/python training/evaluate.py --adapter artifacts/lora-v2 --limit 96
.venv/bin/python training/evaluate.py --adapter artifacts/lora-v2 --dataset data/challenge.jsonl --limit 12 --output artifacts/challenge-v2-evaluation.json
.venv/bin/python training/evaluate.py --adapter artifacts/lora-v2 --dataset data/audit.jsonl --limit 12 --output artifacts/audit-v2-evaluation.json
.venv/bin/python training/prepare_upload.py --adapter artifacts/lora-v2 --output artifacts/cloudflare-upload-v2
```

Google's Gemma model license must be accepted in the Hugging Face account used for download. Do not commit access tokens or model weights. The upload preparation step leaves the evaluated PEFT adapter unchanged and stages only the two files Cloudflare accepts. See the linked documentation for the exact evaluation protocol, deployment steps, limits, and unresolved risks.
