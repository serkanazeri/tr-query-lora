"""Shared training/evaluation contract. The Worker mirrors this schema and compiler."""

import json
import re
from datetime import date, timedelta

MODEL_ID = "google/gemma-2b-it"
REFERENCE_DATE = "2026-09-30"
METRICS = ("order_count", "delayed_count", "revenue", "delivery_days")
GROUPS = ("none", "branch", "city")
PERIODS = ("all", "last_30_days")
CITIES = ("all", "Ankara", "İstanbul", "İzmir")
SYSTEM_PROMPT = (
    "Türkçe operasyon sorusunu yalnızca JSON sorgu planına dönüştür. Açıklama, Markdown ve SQL yazma.\n"
    'Şema: {"metric":"order_count|delayed_count|revenue|delivery_days","group_by":"none|branch|city","period":"all|last_30_days","city":"all|Ankara|İstanbul|İzmir"}\n'
    "Metrikler: order_count tüm sipariş sayısı; delayed_count yalnızca geciken sipariş sayısı; revenue toplam satış tutarı; delivery_days ortalama teslimat günü.\n"
    "İstenen şehir yoksa city=all, grup istenmiyorsa group_by=none, dönem yoksa period=all. Son 30 gün deniyorsa period=last_30_days.\n"
    "Yalnızca bu alanları ve değerleri kullan."
)


def question_prompt(question: str) -> str:
    return f"{SYSTEM_PROMPT}\nSoru: {question}"


def validate_plan(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"metric", "group_by", "period", "city"}:
        raise ValueError("Plan must have exactly four fields")
    expected = {"metric": METRICS, "group_by": GROUPS, "period": PERIODS, "city": CITIES}
    for field, choices in expected.items():
        if value[field] not in choices:
            raise ValueError(f"Invalid {field}: {value[field]}")
    return value


def parse_plan(raw: str) -> dict[str, str]:
    raw = raw.strip()
    if not raw.startswith("{") or not raw.endswith("}"):
        raise ValueError("Not bare JSON")
    return validate_plan(json.loads(raw))


def compile_plan(plan: dict[str, str], reference_date: str = REFERENCE_DATE) -> tuple[str, list[str]]:
    validate_plan(plan)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", reference_date):
        raise ValueError("Invalid date")
    metric = {
        "order_count": "COUNT(*)",
        "delayed_count": "SUM(CASE WHEN status = 'delayed' THEN 1 ELSE 0 END)",
        "revenue": "ROUND(SUM(amount_try), 2)",
        "delivery_days": "ROUND(AVG(delivery_days), 2)",
    }[plan["metric"]]
    group = {"none": None, "branch": "branch", "city": "city"}[plan["group_by"]]
    clauses: list[str] = []
    binds: list[str] = []
    if plan["period"] == "last_30_days":
        clauses.append("order_date >= date(?, '-29 days') AND order_date <= ?")
        binds.extend([reference_date, reference_date])
    if plan["city"] != "all":
        clauses.append("city = ?")
        binds.append(plan["city"])
    sql = f"SELECT {group + ' AS segment' if group else chr(39) + 'Tümü' + chr(39) + ' AS segment'}, {metric} AS value FROM orders"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    if group:
        sql += f" GROUP BY {group}"
    sql += " ORDER BY segment LIMIT 20"
    return sql, binds
