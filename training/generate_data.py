"""Create deterministic synthetic questions; test sentence frames are held out."""

import itertools
import json
import random
from pathlib import Path

from common import CITIES, GROUPS, METRICS, PERIODS, validate_plan

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data"
RNG = random.Random(20261003)

METRIC_PHRASES = {
    "order_count": ("sipariş sayısını", "kaç sipariş olduğunu", "toplam sipariş adedini"),
    "delayed_count": ("geciken sipariş sayısını", "kaç siparişin geciktiğini", "gecikmiş sipariş adedini"),
    "revenue": ("toplam ciroyu", "satış tutarını", "toplam geliri"),
    "delivery_days": ("ortalama teslimat gününü", "ortalama kaç günde teslim edildiğini", "teslimat süresi ortalamasını"),
}
GROUP_PHRASES = {"none": "", "branch": " şubeye göre", "city": " şehre göre"}
PERIOD_PHRASES = {"all": "", "last_30_days": "son 30 günde "}
CITY_PHRASES = {"all": "", "Ankara": "Ankara'daki ", "İstanbul": "İstanbul'daki ", "İzmir": "İzmir'deki "}

TRAIN_FRAMES = (
    "{period}{city}{metric}{group} göster",
    "{period}{city}{metric}{group} listele",
    "Bana {period}{city}{metric}{group} ver",
    "{period}{city}{metric}{group} öğrenmek istiyorum",
)
VALID_FRAMES = ("{period}{city}{metric}{group} raporla",)
TEST_FRAMES = (
    "{period}{city}{metric}{group} nedir?",
)

# Extra training phrasings target the grouping failures observed on the separate
# natural-language challenge set. No challenge question is copied into training.
GROUP_PARAPHRASES = {
    "branch": ((" şubelere ayır", ""), (" şube bazında", " göster"), (" şubelere dağıt", "")),
    "city": ((" şehir bazında", " göster"), (" şehirlere göre", " göster"), (" şehir şehir", " karşılaştır")),
}
PERIOD_PARAPHRASES = ("son 30 günde ", "geçtiğimiz 30 günde ", "son otuz günde ")


def make_row(metric: str, group: str, period: str, city: str, frame: str, phrase_index: int) -> dict:
    plan = validate_plan({"metric": metric, "group_by": group, "period": period, "city": city})
    question = frame.format(period=PERIOD_PHRASES[period], city=CITY_PHRASES[city],
                            metric=METRIC_PHRASES[metric][phrase_index], group=GROUP_PHRASES[group])
    question = question[0].upper() + question[1:]
    return {"question": question, "plan": plan}


def generate(frames: tuple[str, ...], phrase_indices: tuple[int, ...]) -> list[dict]:
    rows = [make_row(*values, frame, phrase_index)
            for values in itertools.product(METRICS, GROUPS, PERIODS, CITIES)
            for frame in frames for phrase_index in phrase_indices]
    unique = {row["question"]: row for row in rows}
    rows = list(unique.values())
    RNG.shuffle(rows)
    return rows


def generate_training_paraphrases() -> list[dict]:
    rows = []
    for metric, group, period, city in itertools.product(METRICS, ("branch", "city"), PERIODS, CITIES):
        for index, (group_text, ending) in enumerate(GROUP_PARAPHRASES[group]):
            period_text = PERIOD_PARAPHRASES[index] if period == "last_30_days" else ""
            metric_text = METRIC_PHRASES[metric][index]
            question = f"{period_text}{CITY_PHRASES[city]}{metric_text}{group_text}{ending}"
            question = question[0].upper() + question[1:]
            rows.append({"question": question, "plan": validate_plan({
                "metric": metric, "group_by": group, "period": period, "city": city,
            })})
    return rows


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    splits = {
        "train": generate(TRAIN_FRAMES, (0, 1)),
        "valid": generate(VALID_FRAMES, (2,)),
        "test": generate(TEST_FRAMES, (1,)),
    }
    splits["train"].extend(generate_training_paraphrases())
    RNG.shuffle(splits["train"])
    # Held-out sentence frames prevent exact question duplicates. Semantic combinations recur.
    sets = {name: {row["question"] for row in rows} for name, rows in splits.items()}
    assert not (sets["train"] & sets["valid"] or sets["train"] & sets["test"] or sets["valid"] & sets["test"])
    for name, rows in splits.items():
        with (OUTPUT / f"{name}.jsonl").open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (OUTPUT / "manifest.json").write_text(json.dumps({
        "seed": 20261003,
        "generation_version": 2,
        "counts": {name: len(rows) for name, rows in splits.items()},
        "synthetic": True,
        "human_reviewed": False,
        "split_method": "held-out sentence frames; metric/group/period/city combinations recur",
        "training_paraphrases": "192 additional grouping and period phrasings; no exact challenge question copied",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({name: len(rows) for name, rows in splits.items()})


if __name__ == "__main__":
    main()
