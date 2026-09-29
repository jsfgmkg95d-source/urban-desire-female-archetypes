"""Read-only, dependency-free retrieval of this repository's research records."""

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote


REPOSITORY_URL = "https://github.com/jsfgmkg95d-source/urban-desire-female-archetypes"
RAW_BASE_URL = "https://raw.githubusercontent.com/jsfgmkg95d-source/urban-desire-female-archetypes/main"
VERSION = "0.1.0"
RELEASE_TAG = "v" + VERSION
CARD_ID_PATTERN = re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)+-\d+")
RULES = {
    "source-rules": "references/source-rules.md",
    "quality-gate": "references/quality-gate.md",
    "archetype-taxonomy": "references/archetype-taxonomy.md",
    "hybridization-rules": "references/hybridization-rules.md",
    "visual-language": "references/visual-language.md",
    "agents": "AGENTS.md",
    "skill": "SKILL.md",
}
LIMITATIONS = [
    "Research preview: tiers and scores are internal assessments, not independent certification.",
    "JSONL is a derived summary. Read the full card and source record before adapting a mechanism.",
    "Source locators and local readback do not prove claim-level verification, originality, or rights clearance.",
    "Age-unknown/minor originals remain non-erotic; explicit-adult H4 is separate ADAPTATION.",
    "Reuse mechanisms, not original plot sequences. These cards do not describe women in general.",
    "Main/release URLs are locators and may differ from this local checkout; raw-local-bytes hashes are local read receipts only.",
    "Original project content is CC-BY-4.0; original code is MIT. Third-party works, translations and quotations are excluded from these grants. See " + REPOSITORY_URL + "/blob/main/COPYRIGHT.md.",
]
LICENSING = {
    "original_content": "CC-BY-4.0",
    "original_code": "MIT",
    "third_party_material": "Excluded from project license grants; original works, translations and quotations retain their own rights.",
    "attribution": "jsfgmkg95d-source / Urban Desire Female Archetypes",
    "scope_url": REPOSITORY_URL + "/blob/main/COPYRIGHT.md",
    "third_party_notices_url": REPOSITORY_URL + "/blob/main/THIRD_PARTY_NOTICES.md",
}
MECHANISM_FIELDS = (
    "long_term_lack", "first_crossing", "immediate_reward", "power_method",
    "jealous_resource", "secret_leverage", "escalation_logic", "fatal_miscalculation",
)
SEARCH_FIELDS = {
    "card_id": ("METADATA", 6), "name_zh": ("METADATA", 6),
    "aliases": ("METADATA", 5), "source_work": ("METADATA", 2),
    "primary_archetype_id": ("INTERPRETATION", 4),
    "secondary_archetype_ids": ("INTERPRETATION", 2),
    **{name: ("INTERPRETATION", 3) for name in MECHANISM_FIELDS},
    "retrieval_capsule.one_line_archetype": ("INTERPRETATION", 3),
    "retrieval_capsule.desire_chain": ("INTERPRETATION", 3),
    "retrieval_capsule.power_interface": ("INTERPRETATION", 2),
    "adult_adaptation_role": ("ADAPTATION", 1),
    "retrieval_capsule.best_urban_container.core_conflict": ("ADAPTATION", 2),
}


class InputError(ValueError):
    """A bounded tool argument is invalid; the caller may correct it."""


class LibraryError(ValueError):
    """The local dataset or its readback files cannot be used safely."""


def reject_constant(value):
    raise ValueError(f"Non-finite JSON number is not allowed: {value}")


def text_argument(value, name, maximum=200):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise InputError(f"{name} must be a nonempty string of at most {maximum} characters")
    if any(ord(char) < 32 and not char.isspace() for char in value):
        raise InputError(f"{name} contains an unsupported control character")
    return value.strip()


def integer_argument(value, name, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise InputError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def normalized(value):
    return unicodedata.normalize("NFKC", value).casefold()


def field_value(record, field):
    current = record
    for part in field.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(part)
    if isinstance(current, list):
        return "；".join(str(item) for item in current)
    if isinstance(current, dict):
        return "；".join(str(item) for item in current.values())
    return current if isinstance(current, str) else ""


class Library:
    def __init__(self, root=None):
        self.root = (Path(root) if root is not None else Path(__file__).resolve().parents[1]).resolve()
        schema_text, _ = self._read("data/archetypes.json")
        summary_text, summary_raw = self._read("data/characters.jsonl")
        try:
            self.schema = json.loads(schema_text, parse_constant=reject_constant)
            self.records = [json.loads(line, parse_constant=reject_constant)
                            for line in summary_text.splitlines() if line.strip()]
            self.archetypes = {item["id"] for item in self.schema["archetypes"]}
            self.source_categories = set(self.schema["enums"]["source_category"])
        except (ValueError, KeyError, TypeError) as error:
            raise LibraryError(f"Invalid local retrieval data: {error}") from error
        self.summary_sha256 = hashlib.sha256(summary_raw).hexdigest()
        self.by_id = {}
        for record in self.records:
            if not isinstance(record, dict):
                raise LibraryError("Each characters.jsonl line must be an object")
            card_id = record.get("card_id")
            if not isinstance(card_id, str) or not CARD_ID_PATTERN.fullmatch(card_id) or card_id in self.by_id:
                raise LibraryError("Duplicate or invalid card_id in local data")
            if record.get("tier") not in ("Gold", "Silver", "Reference") or not isinstance(record.get("layer_completion"), dict):
                raise LibraryError(f"Invalid tier or layer_completion for {card_id}; run validate-library.py")
            self.by_id[card_id] = record
        self.card_paths = {}
        for path in sorted((self.root / "characters").rglob("*.md")):
            if path.name == "README.md":
                continue
            card_id = path.stem.split("_", 1)[0]
            if card_id in self.card_paths:
                raise LibraryError(f"Duplicate character file for {card_id}")
            self.card_paths[card_id] = path.relative_to(self.root).as_posix()
        if set(self.card_paths) != set(self.by_id):
            raise LibraryError("Card files and JSONL IDs differ; run validate-library.py")
        # Resolve boundaries before exposing any search result. No external reads.
        for card_id, path in self.card_paths.items():
            self._safe_path(path)
            self._safe_path(f"sources/{card_id}_sources.md")

    def _safe_path(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise LibraryError(f"Repository readback file missing or outside repository: {relative}")
        return path

    def _read(self, relative):
        path = self._safe_path(relative)
        try:
            raw = path.read_bytes()
            if len(raw) > 1024 * 1024:
                raise LibraryError(f"Readback file exceeds 1 MiB limit: {relative}")
            if raw.startswith(b"\xef\xbb\xbf"):
                raise LibraryError(f"UTF-8 BOM is not allowed: {relative}")
            text = raw.decode("utf-8")
        except (OSError, UnicodeError) as error:
            raise LibraryError(f"Cannot read UTF-8 repository file: {relative}") from error
        return text, raw

    def _document(self, relative, include_text=False):
        text, raw = self._read(relative)
        encoded = quote(relative, safe="/")
        result = {
            "path": relative,
            "github_url": f"{REPOSITORY_URL}/blob/main/{encoded}",
            "raw_url": f"{RAW_BASE_URL}/{encoded}",
            "release_github_url": f"{REPOSITORY_URL}/blob/{RELEASE_TAG}/{encoded}",
            "release_raw_url": f"https://raw.githubusercontent.com/jsfgmkg95d-source/urban-desire-female-archetypes/{RELEASE_TAG}/{encoded}",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "hash_basis": "raw-local-bytes",
        }
        if include_text:
            result["text"] = text
        return result

    def _envelope(self, **fields):
        return {"quality_status": "research-preview", "library_version": VERSION,
                "release_tag": RELEASE_TAG, "repository_url": REPOSITORY_URL,
                "summary_sha256": self.summary_sha256, "summary_hash_basis": "raw-local-bytes",
                "limitations": list(LIMITATIONS), "licensing": dict(LICENSING), **fields}

    def _item(self, record, include_text=False, include_mechanism=True):
        card_id = record["card_id"]
        item = {
            "card_id": card_id, "name_zh": record["name_zh"], "tier": record["tier"],
            "tier_scope": "internal-assessment", "quality_status": "research-preview",
            "source_work": record["source_work"], "source_category": record["source_category"],
            "primary_archetype_id": record["primary_archetype_id"],
            "secondary_archetype_ids": record.get("secondary_archetype_ids", []),
            "adult_status": record["adult_status"], "source_ids": record["source_ids"],
            "card": self._document(self.card_paths[card_id], include_text),
            "source_record": self._document(f"sources/{card_id}_sources.md", include_text),
            "readback_required": not include_text,
        }
        if include_mechanism and record["tier"] != "Reference" and record["layer_completion"].get("M") is True:
            item["mechanism"] = {field: record.get(field, "UNKNOWN") for field in MECHANISM_FIELDS}
            item["mechanism_statement_type"] = "INTERPRETATION"
        return item

    def _filter(self, tier, archetype, source_category, search=False):
        tiers = ("Gold", "Silver") if search else ("Gold", "Silver", "Reference")
        if tier is not None and tier not in tiers:
            raise InputError("tier must be one of " + ", ".join(tiers))
        if archetype is not None and (not isinstance(archetype, str) or archetype not in self.archetypes):
            raise InputError("archetype must be a known archetype ID")
        if source_category is not None and (not isinstance(source_category, str) or source_category not in self.source_categories):
            raise InputError("source_category must be a known source category")
        return [record for record in self.records
                if record["tier"] in tiers and (tier is None or record["tier"] == tier)
                and (archetype is None or archetype in [record["primary_archetype_id"], *record.get("secondary_archetype_ids", [])])
                and (source_category is None or record["source_category"] == source_category)]

    def search(self, query, limit=5, tier=None, archetype=None, source_category=None):
        query = text_argument(query, "query")
        limit = integer_argument(limit, "limit", 1, 20)
        terms = list(dict.fromkeys(normalized(term) for term in re.split(r"[\s,，;；]+", query) if term))
        if len(terms) > 16:
            raise InputError("query must contain at most 16 literal keywords")
        hits = []
        for record in self._filter(tier, archetype, source_category, search=True):
            if record["layer_completion"].get("M") is not True:
                continue
            matched, all_terms, score = [], set(), 0
            for field, (statement_type, weight) in SEARCH_FIELDS.items():
                if field.startswith("retrieval_capsule.") and record["layer_completion"].get("R") is not True:
                    continue
                if field == "adult_adaptation_role" and record["layer_completion"].get("H") is not True:
                    continue
                value = field_value(record, field)
                if normalized(value).strip() in ("", "unknown"):
                    continue
                matched_terms = [term for term in terms if term in normalized(value)]
                if matched_terms:
                    all_terms.update(matched_terms)
                    score += weight * len(matched_terms)
                    matched.append({"field": field, "statement_type": statement_type,
                                    "matched_terms": matched_terms, "excerpt": value[:240],
                                    "reason": "Literal keyword match; confirm meaning in the full card."})
            if matched:
                hits.append((len(all_terms), score, record["card_id"], record, matched, all_terms))
        hits.sort(key=lambda item: (-item[0], -item[1], item[2]))
        results = []
        for coverage, score, _, record, matched, all_terms in hits[:limit]:
            item = self._item(record)
            item.update({"matched_fields": matched, "matched_terms": [term for term in terms if term in all_terms],
                         "unmatched_terms": [term for term in terms if term not in all_terms],
                         "keyword_rank_score": score, "matched_keyword_count": coverage})
            results.append(item)
        return self._envelope(query=query, search_mode="literal-keywords; coverage then weighted field matches; not S scores or semantic search",
                              total_matches=len(hits), returned=len(results), results=results)

    def get(self, card_id):
        card_id = text_argument(card_id, "card_id", 80)
        if not CARD_ID_PATTERN.fullmatch(card_id):
            raise InputError("card_id must be a stable ID, not a filename or path")
        if card_id not in self.by_id:
            raise InputError(f"Unknown card_id: {card_id}")
        return self._envelope(**self._item(self.by_id[card_id], include_text=True))

    def list(self, limit=30, offset=0, tier=None, archetype=None, source_category=None):
        limit = integer_argument(limit, "limit", 1, 100)
        offset = integer_argument(offset, "offset", 0, 10000)
        records = sorted(self._filter(tier, archetype, source_category), key=lambda record: record["card_id"])
        results = [self._item(record, include_mechanism=False) for record in records[offset:offset + limit]]
        return self._envelope(total_records=len(records), offset=offset, returned=len(results), results=results,
                              next_offset=offset + limit if offset + limit < len(records) else None)

    def read_rules(self, name):
        name = text_argument(name, "name", 80)
        if name not in RULES:
            raise InputError("name must be one of: " + ", ".join(RULES))
        return self._envelope(name=name, document=self._document(RULES[name], include_text=True))

    def tool_definitions(self):
        filters = {
            "tier": {"type": "string", "enum": ["Gold", "Silver"]},
            "archetype": {"type": "string", "enum": sorted(self.archetypes)},
            "source_category": {"type": "string", "enum": sorted(self.source_categories)},
        }
        definitions = [
            ("search_archetypes", "Find research-preview mechanism records by literal keywords. No body-feature gallery. Read back selected cards and sources.",
             {**filters, "query": {"type": "string", "minLength": 1, "maxLength": 200},
              "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5}}, ["query"]),
            ("get_archetype", "Read the complete local character card and its source record by stable ID; this is readback, not independent fact verification.",
             {"card_id": {"type": "string", "minLength": 1, "maxLength": 80, "pattern": CARD_ID_PATTERN.pattern}}, ["card_id"]),
            ("list_archetypes", "List registrations with internal tiers. Reference remains research material, not a production recommendation.",
             {**filters, "tier": {"type": "string", "enum": ["Gold", "Silver", "Reference"]},
              "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 30},
              "offset": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 0}}, []),
            ("read_rules", "Read an allowlisted repository rule document. No arbitrary paths or commands.",
             {"name": {"type": "string", "enum": list(RULES)}}, ["name"]),
        ]
        return [{"name": name, "description": description,
                 "inputSchema": {"type": "object", "properties": properties,
                                 "required": required, "additionalProperties": False},
                 "annotations": {"readOnlyHint": True, "destructiveHint": False,
                                 "idempotentHint": True, "openWorldHint": False}}
                for name, description, properties, required in definitions]

    def call_tool(self, name, arguments):
        if not isinstance(arguments, dict):
            raise InputError("tool arguments must be an object")
        definitions = {tool["name"]: tool["inputSchema"] for tool in self.tool_definitions()}
        if name not in definitions:
            raise InputError(f"Unknown tool: {name}")
        schema = definitions[name]
        extra = arguments.keys() - schema["properties"].keys()
        missing = set(schema["required"]) - arguments.keys()
        if extra or missing:
            raise InputError(f"Tool argument mismatch: unknown={sorted(extra)}, missing={sorted(missing)}")
        method = {"search_archetypes": self.search, "get_archetype": self.get,
                  "list_archetypes": self.list, "read_rules": self.read_rules}[name]
        return method(**arguments)
