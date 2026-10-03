# TR-Query

**A measurable LoRA experiment for Turkish analytics questions.** The app maps a question about fictional retail operations to a four-field query plan. It compares the same Gemma 2B base model before and after LoRA adaptation, then shows the validated plan, compiled read-only SQL, and result over synthetic data.

> **Current status:** The local app and training pipeline are implemented. A trained adapter, evaluation results, and a public demo URL are not yet verified. They will be added only after actual training and deployment.

[Türkçe](README.md) · [Architecture](docs/architecture.md) · [Evaluation](docs/evaluation.md) · [Operations](docs/operations.md)

## What this demonstrates

- A reproducible synthetic dataset with distinct training, validation, and held-out wording templates.
- Standard LoRA, not QLoRA: rank 8 on `q_proj` and `v_proj`, with unquantized base weights.
- A matched base-versus-adapter comparison using the same prompt and decoding settings.
- Strict plan validation and a fixed SQL compiler. Model-authored SQL is never executed.
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

Open `http://localhost:8789`. The comparison remains disabled until a trained LoRA adapter is configured. Local Wrangler AI bindings access the remote AI service and may consume the shared free quota.

```bash
python3 training/generate_data.py
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python training/train.py --steps 240
.venv/bin/python training/evaluate.py --limit 96
.venv/bin/python training/evaluate.py --dataset data/challenge.jsonl --limit 12 --output artifacts/challenge-evaluation.json
.venv/bin/python training/prepare_upload.py
```

Google's Gemma model license must be accepted in the Hugging Face account used for download. Do not commit access tokens or model weights. The upload preparation step leaves the evaluated PEFT adapter unchanged and stages only the two files Cloudflare accepts. See the linked documentation for the exact evaluation protocol, deployment steps, limits, and unresolved risks.
