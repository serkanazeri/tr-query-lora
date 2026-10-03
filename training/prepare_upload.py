"""Stage only the two PEFT files accepted by Cloudflare Workers AI."""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, default=ROOT / "artifacts" / "lora")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "cloudflare-upload")
    args = parser.parse_args()

    config_path = args.adapter / "adapter_config.json"
    weights_path = args.adapter / "adapter_model.safetensors"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_model = config.get("base_model_name_or_path")
    local_model = (ROOT / "artifacts" / "base-model").resolve()
    if source_model != "google/gemma-2b-it" and Path(source_model or "").resolve() != local_model:
        raise SystemExit("Adapterın temel modeli google/gemma-2b-it olmalı.")
    if config.get("r", 999) > 8 or weights_path.stat().st_size >= 300_000_000:
        raise SystemExit("Adapter Cloudflare rank veya 300 MB sınırını aşıyor.")
    args.output.mkdir(parents=True, exist_ok=True)
    config["base_model_name_or_path"] = "google/gemma-2b-it"
    config["model_type"] = "gemma"
    (args.output / "adapter_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    shutil.copy2(weights_path, args.output / weights_path.name)
    print(f"Cloudflare upload bundle ready: {args.output}")


if __name__ == "__main__":
    main()
