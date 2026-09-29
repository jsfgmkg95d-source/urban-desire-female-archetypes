#!/usr/bin/env python3
"""Validate local structure and derivation, not source truth or originality.

Character cards and sources are read only. Gold, Silver, and Reference follow
different completeness gates; a batch size or historical filename is not a gate.
"""

import argparse
import json
import math
import re
import runpy
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit


BUILDER = runpy.run_path(str(Path(__file__).with_name("build-indexes.py")))
read_utf8 = BUILDER["read_utf8"]
ARRAY_FIELDS = (
    "aliases", "secondary_archetype_ids", "visual_signature", "visual_plot_functions",
    "plot_engine_ids", "urban_preserve", "adult_visual_signature", "adult_identity_body_contrast",
    "adult_visual_plot_functions", "hybridization_slots", "source_ids",
)
STRING_FIELDS = (
    "card_id", "schema_version", "tier", "name_zh", "source_category", "source_work",
    "primary_archetype_id", "adult_status", "long_term_lack", "first_crossing",
    "immediate_reward", "power_method", "jealous_resource", "secret_leverage",
    "escalation_logic", "fatal_miscalculation", "adult_adaptation_role",
    "adult_low_register_first_glance", "anti_clone_result", "archetype_uniqueness_statement",
)
M_STAGES = ("长期匮乏", "诱因", "第一次越界", "即时奖励", "自我合理化", "风险提高", "继续加码", "最终代价")
LIMITATION = "Structural validation does not verify source truth, age evidence, R semantic fidelity, similarity, originality, or rights."


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strings(value, label):
    require(isinstance(value, list), f"{label} must be an array")
    require(all(isinstance(item, str) and item.strip() for item in value), f"{label} must contain nonempty strings")
    require(len(set(value)) == len(value), f"{label} contains duplicate entries")


def nonempty(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be a nonempty string")


def number(value, minimum, maximum, label):
    require(type(value) in (int, float) and math.isfinite(value), f"{label} must be a finite number")
    require(minimum <= value <= maximum, f"{label} must be in [{minimum}, {maximum}]")


def age_range(value, minimum, label):
    """Accept an explicit age or closed age interval; never infer an adult age."""
    if type(value) in (int, float):
        number(value, minimum, float("inf"), label)
        return value, value
    require(isinstance(value, str), f"{label} must be an explicit age or age interval")
    match = re.fullmatch(r"(\d+)\s*(?:岁?\s*[-—–~至到]\s*(\d+))?\s*岁?", value.strip().strip("`"))
    require(match is not None, f"{label} must be an explicit age or closed interval, e.g. 28 or 25-30")
    lower, upper = int(match[1]), int(match[2] or match[1])
    require(minimum <= lower <= upper, f"{label} is below the adult design age or has a reversed interval")
    return lower, upper


def metadata(text):
    block = text.split("\n# F =", 1)[0].split("\n## 来源登记", 1)[0]
    result = {}
    for match in re.finditer(r"^\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|\s*$", block, re.M):
        value = match[2]
        if value.startswith("`") and value.endswith("`"):
            value = value[1:-1]
        result[match[1]] = value
    return result


def section(text, layer):
    match = re.search(rf"^# {layer}\s*=.*$", text, re.M)
    if not match:
        return ""
    end = re.search(r"^# ", text[match.end():], re.M)
    return text[match.start():match.end() + end.start()] if end else text[match.start():]


def check_capsule(record, schema):
    capsule = record["retrieval_capsule"]
    require(isinstance(capsule, dict), "retrieval_capsule must be an object")
    if not record["layer_completion"]["R"]:
        return
    constraints = schema["constraints"]
    for field in ("one_line_archetype", "desire_chain", "machine_call_string"):
        nonempty(capsule.get(field), "retrieval_capsule." + field)
    require(len(capsule["one_line_archetype"]) <= constraints["retrieval_one_line_max_chars"], "R1 exceeds schema length limit")
    for field, keys in (
        ("visual_signature", ("identity_body_contrast", "clothing_effect")),
        ("power_interface", ("power_method", "secret_use", "feared_resource_loss")),
        ("best_urban_container", ("identity", "marital_status", "class_position", "core_conflict")),
        ("hybrid_recommendation", ("inherit", "conflict", "never_copy_together")),
    ):
        require(isinstance(capsule.get(field), dict), f"R {field} must be an object")
        for key in keys:
            nonempty(capsule[field].get(key), f"R {field}.{key}")
    points = capsule["visual_signature"].get("memory_points")
    strings(points, "R2 memory_points")
    require(constraints["core_body_memory_points_min"] <= len(points) <= constraints["core_body_memory_points_max"], "R2 memory point count invalid")
    strings(capsule.get("forbidden_as"), "R7 forbidden_as")
    require(len(capsule["forbidden_as"]) == constraints["retrieval_forbidden_as_required"], "R7 item count invalid")
    lower, upper = age_range(capsule["best_urban_container"].get("age"), constraints["adult_adaptation_age_min"], "R5 age")
    h4_lower, h4_upper = age_range(record["adult_adaptation_age"], constraints["adult_adaptation_age_min"], "H4 age")
    require(h4_lower <= lower <= upper <= h4_upper, "R5 age is outside the H4 design age")


def check_record(record, schema, all_ids, path, root, stats):
    card_id = record["card_id"]
    constraints, enums = schema["constraints"], schema["enums"]
    for field in schema["record_contract"]["machine_retrieval_fields"] + ["schema_version"]:
        require(field in record, f"Missing machine field: {field}")
    for field in STRING_FIELDS:
        require(isinstance(record.get(field), str), f"{field} must be a string (use UNKNOWN for uncertain text)")
    for field in ARRAY_FIELDS:
        strings(record.get(field), field)
    for field in ("scores", "layer_completion", "adult_clothing_contrast", "retrieval_capsule"):
        require(isinstance(record.get(field), dict), f"{field} must be an object")
    for field in ("tier", "adult_status", "source_category"):
        require(record[field] in enums[field], f"Invalid {field}: {record[field]}")
    require(record["schema_version"] == schema["schema_version"], "Record/schema versions differ")
    valid_archetypes = {item["id"] for item in schema["archetypes"]}
    require(record["primary_archetype_id"] in valid_archetypes, "Invalid primary archetype")
    require(set(record["secondary_archetype_ids"]) <= valid_archetypes, "Invalid secondary archetype")
    require(len(record["secondary_archetype_ids"]) <= constraints["secondary_archetypes_max"], "Too many secondary archetypes")
    require(record["primary_archetype_id"] not in record["secondary_archetype_ids"], "Primary archetype duplicated in secondary archetypes")
    for field in ("visual_plot_functions", "adult_visual_plot_functions"):
        require(set(record[field]) <= set(enums["visual_plot_function"]), f"Invalid {field}")
    require(set(record["hybridization_slots"]) <= set(schema["hybridization_slots"]), "Invalid hybridization slot")
    require(record["anti_clone_result"] in enums["quality_result"], "Invalid anti_clone_result")

    completion = record["layer_completion"]
    layers = schema["record_contract"]["required_layers"]
    require(all(type(completion.get(layer)) is bool for layer in layers), "layer_completion must contain a boolean for every layer")
    required = layers if record["tier"] == "Gold" else ["F", "M", "P", "H", "X", "S"] if record["tier"] == "Silver" else ["F"]
    for layer in required:
        require(completion[layer], f"{record['tier']} requires completed layer {layer}")
    for dimension in schema["score_dimensions"]:
        if completion["S"]:
            number(record["scores"].get(dimension), constraints["score_min"], constraints["score_max"], "score " + dimension)
    if completion["S"]:
        number(record["scores"].get("evidence_confidence"), constraints["evidence_confidence_min"], constraints["evidence_confidence_max"], "evidence_confidence")
    neighbor = record.get("nearest_neighbor_card_id")
    require(neighbor is None or isinstance(neighbor, str), "nearest_neighbor_card_id must be a string or null")
    if neighbor:
        require(neighbor in all_ids and neighbor != card_id, "Nearest neighbor must be another existing card")
    if record["tier"] == "Gold":
        require(bool(neighbor), "Gold requires a real nearest neighbor")
        require(record["anti_clone_result"] == "PASS", "Gold Anti-Clone must be PASS")
        require(len(record["plot_engine_ids"]) >= constraints["gold_plot_engines_min"], "Gold plot engine count too low")
        nonempty(record["archetype_uniqueness_statement"], "Gold uniqueness statement")
        require(len(record["archetype_uniqueness_statement"]) <= constraints["gold_uniqueness_statement_max_chars"], "Gold uniqueness statement too long")
    elif record["tier"] == "Silver":
        require(len(record["plot_engine_ids"]) >= 1, "Silver requires at least one plot engine")

    text = read_utf8(path)
    meta = metadata(text)
    for field in schema["record_contract"]["required_metadata"]:
        nonempty(meta.get(field), "Card metadata " + field)
    for field in ("card_id", "schema_version", "tier", "name_zh", "source_category", "primary_archetype_id", "adult_status"):
        require(meta[field] == record[field], f"Card metadata / summary mismatch: {field}")
    require(meta["status"] in enums["record_status"], "Invalid card status")
    require(json.loads(meta["secondary_archetype_ids"]) == record["secondary_archetype_ids"], "Card secondary archetypes differ from summary")
    date.fromisoformat(meta["last_verified"])
    require(path.relative_to(root / "characters").parts[0] == record["source_category"], "Character path/category mismatch")
    for layer in layers:
        if completion[layer]:
            require(bool(section(text, layer)), f"Missing completed card layer {layer}")
    if record["tier"] == "Silver":
        require(bool(section(text, "V")), "Silver requires a V section (non-erotic when original age is unknown/minor)")
        require(bool(record["visual_signature"] and record["visual_plot_functions"]), "Silver requires basic V recognition and plot functions")
        require(bool(section(text, "A")) and "签名" in section(text, "A"), "Silver requires an initial A signature; full Gold audit is not required")
    if record["adult_status"] != "CONFIRMED_ADULT" and section(text, "V"):
        visual = section(text, "V")
        require(re.search(r"允许直白身体分析：\s*`NO`", visual), "Minor/unknown original V body analysis must be closed")
        require("NOT_APPLICABLE：年龄门未通过" in visual, "Minor/unknown original V first glance must be NOT_APPLICABLE")
    if completion["M"]:
        for stage in M_STAGES:
            require(re.search(rf"^\|\s*{stage}\s*\|", section(text, "M"), re.M), f"Missing M stage: {stage}")

    h4_present = (record["adult_adaptation_role"] not in ("", "UNKNOWN")
                  or bool(record["adult_visual_signature"])
                  or record["adult_adaptation_age"] not in (None, "", "UNKNOWN")
                  or bool(re.search(r"^## H4\.", section(text, "H"), re.M)))
    if h4_present or record["tier"] == "Gold":
        summary_age = age_range(record["adult_adaptation_age"], constraints["adult_adaptation_age_min"], "H4 age")
        for field in ("adult_adaptation_role", "adult_low_register_first_glance"):
            nonempty(record[field], field)
        require(constraints["adult_adaptation_visual_signature_min"] <= len(record["adult_visual_signature"]) <= constraints["adult_adaptation_visual_signature_max"], "H4 visual signature count invalid")
        require(bool(record["adult_identity_body_contrast"]), "H4 identity/body contrast missing")
        require(bool(record["adult_visual_plot_functions"]), "H4 visual plot function missing")
        for key in ("public", "maximum", "danger"):
            nonempty(record["adult_clothing_contrast"].get(key), "H4 clothing " + key)
        h4 = section(text, "H")
        require(re.search(r"^## H4\.\s+明确成年现代(?:都市)?视觉移植\s*$", h4, re.M), "Missing H4 heading")
        card_age = re.search(r"^\|\s*`adaptation_age`\s*\|\s*(.*?)\s*\|\s*$", h4, re.M)
        require(card_age is not None, "Card H4 adaptation_age is missing")
        require(age_range(card_age[1], constraints["adult_adaptation_age_min"], "Card H4 age") == summary_age, "Card H4 age differs from machine summary")
        require(re.search(r"`adaptation_adult_status`\s*\|\s*`DESIGNATED_ADULT`", h4), "H4 adult status missing")
        require("是否把 H4 设计倒填为原著事实：`NO`" in h4, "H4 reverse-pollution gate missing")
        require("ADAPTATION" in h4, "H4 must be marked ADAPTATION")

    for engine in record["plot_engine_ids"]:
        require(re.fullmatch(re.escape(card_id) + r"-P\d+", engine), f"Invalid plot engine ID: {engine}")
        require(engine in section(text, "P"), f"Plot engine ID absent from P: {engine}")
    if completion["S"]:
        scores_text = section(text, "S")
        for dimension in schema["score_dimensions"]:
            match = re.search(rf"^\|\s*`{dimension}`\s*\|\s*(\d+(?:\.\d+)?)\s*\|", scores_text, re.M)
            require(match and float(match[1]) == record["scores"][dimension], "Card S / score summary mismatch: " + dimension)
        confidence = re.search(r"`evidence_confidence`[：:\s]*`(\d+)`", scores_text)
        require(confidence and int(confidence[1]) == record["scores"]["evidence_confidence"], "Card S / evidence_confidence summary mismatch")
    if record["tier"] == "Gold":
        require(neighbor in section(text, "A"), "Gold nearest neighbor absent from card A")
        answers = re.findall(r"^\|\s*([1-9]|1[0-2])\s*\|", text, re.M)
        require(sorted(map(int, answers)) == list(range(1, constraints["gold_questions_required"] + 1)), "Gold twelve-question rows incomplete/duplicated")
        require(re.search(r"^# 母体唯一性声明", text, re.M), "Gold uniqueness heading missing")
    check_capsule(record, schema)
    if completion["R"]:
        for item in range(1, 9):
            require(re.search(rf"^## R{item}\.", section(text, "R"), re.M), f"Missing R{item} section")

    source_path = root / "sources" / f"{card_id}_sources.md"
    require(source_path.is_file(), "Missing source file")
    require(source_path.resolve().is_relative_to(root.resolve()), "Source path escapes repository")
    source = read_utf8(source_path)
    require(bool(record["source_ids"]), "At least one source_id is required")
    for source_id in record["source_ids"]:
        require(re.fullmatch(re.escape(card_id) + r"-S\d+", source_id), f"Invalid source_id: {source_id}")
        require(re.search(rf"^\|\s*`{re.escape(source_id)}`\s*\|", source, re.M), f"source_id absent from source table: {source_id}")
    fact_rows = re.findall(r"^\|\s*`F-(?:[A-Z]+-)?\d+`\s*\|.*$", section(text, "F"), re.M)
    require(bool(fact_rows), "F has no source-located fact rows")
    for row in fact_rows:
        ids = re.findall(re.escape(card_id) + r"-S\d+", row)
        require(ids and set(ids) <= set(record["source_ids"]), "F fact lacks a declared source locator: " + row)
        if "对应来源定位" in row:
            stats["fact_locator_placeholders"] += 1
            stats["placeholder_cards"].add(card_id)
    stats["fact_rows"] += len(fact_rows)


def check_links(root):
    files, count = 0, 0
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.relative_to(root).parts:
            continue
        text = read_utf8(path)
        files += 1
        text = re.sub(r"^(`{3,}|~{3,}).*?^\1\s*$", "", text, flags=re.M | re.S)
        for match in re.finditer(r"\]\((<[^>\n]+>|[^)\n]+)\)", text):
            target = match[1]
            target = target[1:-1] if target.startswith("<") else target.split(' "', 1)[0].split(" '", 1)[0]
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            require(resolved.is_relative_to(root), f"Local Markdown link escapes repository in {path.relative_to(root)}: {target}")
            require(resolved.exists(), f"Broken local Markdown link in {path.relative_to(root)}: {target}")
            count += 1
    return files, count


def validate(root, report):
    schema, records = BUILDER["load_library"](root)
    for key in ("record_contract", "enums", "constraints"):
        require(isinstance(schema.get(key), dict), f"Schema {key} must be an object")
    for key in ("archetypes", "score_dimensions", "hybridization_slots", "character_records"):
        require(isinstance(schema.get(key), list), f"Schema {key} must be an array")
    nonempty(schema.get("schema_version"), "Schema schema_version")
    ids = [item.get("id") for item in schema["archetypes"] if isinstance(item, dict)]
    strings(ids, "Schema archetype IDs")
    require(len(ids) == len(schema["archetypes"]), "Malformed archetype definition")
    for key in ("required_layers", "required_metadata", "machine_retrieval_fields"):
        strings(schema["record_contract"].get(key), "Schema record_contract." + key)
    require(set(schema["record_contract"]["required_layers"]) == set("FVMPHXSAR"), "Schema must declare F/V/M/P/H/X/S/A/R")
    for key in ("tier", "adult_status", "source_category", "visual_plot_function", "quality_result", "record_status"):
        strings(schema["enums"].get(key), "Schema enums." + key)
    paths = BUILDER["card_files"](root, records)
    report.update({"records": len(records), "tiers": dict(sorted(Counter(str(r.get("tier", "MISSING")) for r in records).items())), "character_cards": len(paths)})
    stats = {"fact_rows": 0, "fact_locator_placeholders": 0, "placeholder_cards": set()}
    all_ids = {r["card_id"] for r in records}
    for record in records:
        try:
            check_record(record, schema, all_ids, paths[record["card_id"]], root, stats)
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            raise ValueError(f"{record['card_id']}: {error}") from error
    require(schema["character_records"] == BUILDER["character_cache"](records), "character_records cache differs from JSONL (run build-indexes.py)")
    source_ids = {path.stem[:-8] for path in (root / "sources").glob("*_sources.md")}
    require(source_ids == all_ids, "Source files / summary IDs differ")
    report["source_records"] = len(source_ids)
    report["fact_rows_with_source_ids"] = stats["fact_rows"]
    report["fact_locator_placeholder_rows"] = stats["fact_locator_placeholders"]
    report["fact_locator_placeholder_cards"] = sorted(stats["placeholder_cards"])
    if stats["fact_locator_placeholders"]:
        report["warnings"].append(f"{stats['fact_locator_placeholders']} F rows use generic locator text; source IDs exist, but claim-level precision requires manual review.")
    audits = []
    for path in sorted((root / "batches").glob("*.md")):
        text = read_utf8(path)
        if "`audit_id`" in text or "`batch_id`" in text:
            audits.append((path, text))
    if records:
        require(bool(audits), "No batch/audit record found")
    for record in records:
        if record["tier"] == "Gold":
            require(any(record["card_id"] in text for _, text in audits), f"Gold has no batch/audit reference: {record['card_id']}")
    report["audit_records"] = len(audits)
    signatures = [tuple(r["adult_visual_signature"]) for r in records if r["adult_visual_signature"]]
    require(len(set(signatures)) == len(signatures), "Duplicate complete H4 visual signature; manual Anti-Clone review required")
    if len(signatures) >= 10:
        focused = Counter(signature[0] for signature in signatures)
        if max(focused.values()) > len(signatures) * 0.3:
            report["warnings"].append("One exact first visual memory point exceeds 30%; the quality gate requires manual review of differentiation.")
    outputs = BUILDER["generated_indexes"](root, schema, records, paths)
    report["generated_indexes"] = len(outputs)
    report["stale_outputs"] = BUILDER["stale_outputs"](root, schema, records, outputs)
    require(not report["stale_outputs"], "Generated outputs are stale: " + ", ".join(report["stale_outputs"]) + " (run build-indexes.py)")
    report["markdown_files"], report["local_markdown_links"] = check_links(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print one machine-readable result object")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Repository root (default: script location)")
    args = parser.parse_args()
    report = {"status": "FAILED", "errors": [], "warnings": [], "limitations": LIMITATION}
    try:
        validate(args.root.resolve(), report)
        report["status"] = "PASSED"
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError) as error:
        report["errors"].append(str(error))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"VALIDATION {report['status']}: {report.get('records', 0)} records; local structure and generated outputs.")
        for message in report["errors"]:
            print("ERROR: " + message)
        for message in report["warnings"]:
            print("REVIEW: " + message)
        print(LIMITATION)
    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
