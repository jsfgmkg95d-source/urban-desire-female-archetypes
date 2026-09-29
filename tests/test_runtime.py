"""Useful retrieval, readback and wire-protocol regressions; stdlib unittest."""

import hashlib
import io
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from library import InputError, Library, LibraryError, SEARCH_FIELDS

MCP = runpy.run_path(str(ROOT / "scripts/mcp-server.py"))


def request(request_id, method, params=None):
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


def initialize(request_id=1, version="2025-11-25"):
    return request(request_id, "initialize", {"protocolVersion": version, "capabilities": {},
                                            "clientInfo": {"name": "unittest", "version": "1.0"}})


def initialized():
    return {"jsonrpc": "2.0", "method": "notifications/initialized"}


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = Library(ROOT)

    def test_real_query_mechanism_reasons_and_links(self):
        result = self.library.search("秘密 退出", limit=3)
        self.assertEqual(result["results"][0]["card_id"], "CN-SHZ-001")
        self.assertEqual(result["returned"], 3)
        self.assertEqual(result["quality_status"], "research-preview")
        self.assertEqual(result["library_version"], "0.1.0")
        self.assertEqual(result["release_tag"], "v0.1.0")
        self.assertEqual(result["licensing"]["original_content"], "CC-BY-4.0")
        self.assertEqual(result["licensing"]["original_code"], "MIT")
        self.assertIn("Excluded", result["licensing"]["third_party_material"])
        self.assertIn("not S scores", result["search_mode"])
        for item in result["results"]:
            self.assertEqual(item["matched_terms"], ["秘密", "退出"])
            self.assertTrue(item["readback_required"])
            self.assertEqual(item["tier_scope"], "internal-assessment")
            self.assertTrue(item["matched_fields"])
            self.assertTrue(all(field["reason"] and field["statement_type"] for field in item["matched_fields"]))
            for document in (item["card"], item["source_record"]):
                self.assertTrue((ROOT / document["path"]).is_file())
                self.assertIn("/main/", document["raw_url"])
                self.assertIn("/v0.1.0/", document["release_raw_url"])
                self.assertEqual(document["hash_basis"], "raw-local-bytes")
                self.assertNotIn("text", document)

    def test_filters_aliases_and_no_match(self):
        self.assertEqual(self.library.search("潘六姐")["results"][0]["card_id"], "CN-JPM-001")
        result = self.library.search("秘密", tier="Gold", source_category="chinese-classics")
        self.assertTrue(result["results"])
        self.assertTrue(all(item["tier"] == "Gold" and item["source_category"] == "chinese-classics" for item in result["results"]))
        result = self.library.list(tier="Silver", archetype="power-queen", source_category="mythology-and-epics")
        self.assertEqual([item["card_id"] for item in result["results"]], ["MY-OD-001"])
        self.assertEqual(self.library.search("__no_archetype_hit__")["returned"], 0)

    def test_complete_card_and_source_readback(self):
        result = self.library.get("CN-SHZ-001")
        self.assertFalse(result["readback_required"])
        self.assertIn("# F =", result["card"]["text"])
        self.assertIn("# R =", result["card"]["text"])
        self.assertIn("CN-SHZ-001-S01", result["source_record"]["text"])
        for document in (result["card"], result["source_record"]):
            raw = (ROOT / document["path"]).read_bytes()
            self.assertEqual(document["text"], raw.decode("utf-8"))
            self.assertEqual(document["sha256"], hashlib.sha256(raw).hexdigest())

    def test_default_projection_is_not_a_body_gallery(self):
        self.assertFalse(any("visual" in field or "first_glance" in field for field in SEARCH_FIELDS))
        result = self.library.search("杜丽娘")
        self.assertEqual(result["results"][0]["adult_status"], "CONFIRMED_MINOR")
        serialized = json.dumps(result, ensure_ascii=False)
        for field in ("adult_visual_signature", "memory_points", "adult_low_register_first_glance", "scores"):
            self.assertNotIn('"' + field + '"', serialized)
        self.assertIn("NOT_APPLICABLE：年龄门未通过", self.library.get("CN-MDT-001")["card"]["text"])

    def test_reference_and_incomplete_capsule_not_recommended(self):
        library = Library(ROOT)
        record = library.by_id["CN-JPM-001"]
        record["tier"] = "Reference"
        self.assertEqual(library.search("潘金莲")["returned"], 0)
        listed = library.list(tier="Reference")["results"]
        self.assertEqual(listed[0]["card_id"], "CN-JPM-001")
        self.assertNotIn("mechanism", listed[0])
        record["tier"] = "Silver"
        record["layer_completion"]["R"] = False
        record["retrieval_capsule"]["one_line_archetype"] = "unreviewed-capsule-uniquetoken"
        self.assertEqual(library.search("unreviewed-capsule-uniquetoken")["returned"], 0)

    def test_bounded_inputs_and_path_traversal(self):
        cases = [
            (self.library.search, {"query": "秘密", "limit": True}),
            (self.library.search, {"query": "秘密", "limit": 21}),
            (self.library.search, {"query": "x" * 201}),
            (self.library.search, {"query": " ".join("term" + str(i) for i in range(17))}),
            (self.library.search, {"query": "秘密", "tier": "Reference"}),
            (self.library.search, {"query": "秘密", "source_category": {}}),
            (self.library.list, {"limit": 101}),
            (self.library.list, {"offset": -1}),
            (self.library.get, {"card_id": "../../AGENTS.md"}),
            (self.library.get, {"card_id": "CN-NOPE-999"}),
            (self.library.read_rules, {"name": "../AGENTS.md"}),
            (self.library.call_tool, {"name": "get_archetype", "arguments": {"path": "AGENTS.md"}}),
        ]
        for function, args in cases:
            with self.subTest(args=args), self.assertRaises(InputError):
                function(**args)
        with self.assertRaises(LibraryError):
            self.library._read("../AGENTS.md")

    def test_rules_pagination_and_read_only_bytes(self):
        paths = list((ROOT / "characters").rglob("*.md")) + list((ROOT / "sources").glob("*.md"))
        paths += [ROOT / "data/characters.jsonl", ROOT / "data/archetypes.json"]
        before = {path: hashlib.sha256(path.read_bytes()).digest() for path in paths}
        rules = self.library.read_rules("source-rules")
        self.assertIn("UNKNOWN", rules["document"]["text"])
        first = self.library.list(limit=2)
        second = self.library.list(limit=2, offset=first["next_offset"])
        self.assertFalse(set(item["card_id"] for item in first["results"]) & set(item["card_id"] for item in second["results"]))
        self.library.search("秘密 退出")
        self.library.get("CN-SHZ-001")
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).digest() for path in paths})

    def test_cli_works_outside_checkout_and_emits_json(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/archetypes.py"), "search", "--query", "秘密 退出", "--limit", "3"],
                                cwd=tempfile.gettempdir(), capture_output=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["results"][0]["card_id"], "CN-SHZ-001")
        invalid = subprocess.run([sys.executable, str(ROOT / "scripts/archetypes.py"), "get", "--id", "../AGENTS.md"],
                                 cwd=tempfile.gettempdir(), capture_output=True, encoding="utf-8", timeout=15)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("stable ID", json.loads(invalid.stdout)["error"])


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.server = MCP["Server"](Library(ROOT))

    def ready(self):
        self.server.handle(initialize())
        self.assertIsNone(self.server.handle(initialized()))

    def test_version_negotiation_lifecycle_ping_and_notifications(self):
        self.assertEqual(self.server.handle(request(10, "ping"))["result"], {})
        before = self.server.handle(request(11, "tools/list"))
        self.assertEqual(before["error"]["code"], -32002)
        reply = self.server.handle(initialize(version="2025-06-18"))
        self.assertEqual(reply["result"]["protocolVersion"], "2025-06-18")
        self.assertIsNone(self.server.handle(initialized()))
        self.assertIsNone(self.server.handle({"jsonrpc": "2.0", "method": "notifications/unknown", "params": {}}))
        self.assertEqual(len(self.server.handle(request(2, "tools/list"))["result"]["tools"]), 4)
        future = MCP["Server"](Library(ROOT)).handle(initialize(version="2026-07-28"))
        self.assertEqual(future["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(self.server.handle(initialize(3))["error"]["code"], -32600)

    def test_invalid_json_rpc_and_tool_argument_types(self):
        for message in ([], None, {"jsonrpc": "1.0", "id": 1, "method": "ping"},
                        request(True, "ping"), request(None, "ping"), request(1.5, "ping")):
            with self.subTest(message=message):
                self.assertEqual(self.server.handle(message)["error"]["code"], -32600)
        self.assertEqual(self.server.handle(request(2, "unknown"))["error"]["code"], -32601)
        self.assertEqual(self.server.handle(request(3, "initialize", []))["error"]["code"], -32602)
        self.ready()
        for params in ({"name": []}, {"name": {}}, {"name": "get_archetype", "arguments": []}):
            self.assertEqual(self.server.handle(request(4, "tools/call", params))["error"]["code"], -32602)
        for args in ({"query": "秘密", "limit": True}, {"query": "秘密", "path": "../AGENTS.md"}, {"query": []}):
            result = self.server.handle(request(5, "tools/call", {"name": "search_archetypes", "arguments": args}))["result"]
            self.assertTrue(result["isError"])
            self.assertEqual(result["structuredContent"]["error"]["code"], "invalid_input")
        traversal = self.server.handle(request(6, "tools/call", {"name": "read_rules", "arguments": {"name": "../../AGENTS.md"}}))
        self.assertTrue(traversal["result"]["isError"])

    def test_frame_errors_stay_json_and_recover(self):
        incoming = b"{bad-json\n\xff\n" + b"x" * (MCP["MAX_REQUEST_BYTES"] + 1) + b"\n"
        incoming += json.dumps(request(9, "ping")).encode("utf-8") + b"\n"
        output = io.BytesIO()
        MCP["serve"](io.BytesIO(incoming), output, self.server)
        frames = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([frame["error"]["code"] for frame in frames[:-1]], [-32700, -32700, -32600])
        self.assertEqual(frames[-1], {"jsonrpc": "2.0", "id": 9, "result": {}})

    def test_real_stdio_handshake_discovery_search_and_full_readback(self):
        messages = [initialize(), initialized(), request(2, "tools/list"),
                    request(3, "tools/call", {"name": "search_archetypes", "arguments": {"query": "秘密 退出", "limit": 3}}),
                    request(4, "tools/call", {"name": "get_archetype", "arguments": {"card_id": "CN-SHZ-001"}}),
                    {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 999}},
                    request(5, "ping"), request(6, "tools/call", {"name": "read_rules", "arguments": {"name": "source-rules"}}),
                    request(7, "tools/call", {"name": "list_archetypes", "arguments": {"limit": 1, "tier": "Gold"}})]
        payload = "".join(json.dumps(message, ensure_ascii=False) + "\n" for message in messages)
        process = subprocess.run([sys.executable, str(ROOT / "scripts/mcp-server.py")], input=payload,
                                 cwd=tempfile.gettempdir(), capture_output=True, encoding="utf-8", timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        frames = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([frame["id"] for frame in frames], list(range(1, 8)))
        tools = frames[1]["result"]["tools"]
        self.assertEqual({tool["name"] for tool in tools}, {"search_archetypes", "get_archetype", "list_archetypes", "read_rules"})
        self.assertTrue(all(tool["annotations"]["readOnlyHint"] for tool in tools))
        search = frames[2]["result"]
        self.assertEqual(json.loads(search["content"][0]["text"]), search["structuredContent"])
        self.assertEqual(search["structuredContent"]["results"][0]["card_id"], "CN-SHZ-001")
        readback = frames[3]["result"]["structuredContent"]
        self.assertIn("# F =", readback["card"]["text"])
        self.assertIn("CN-SHZ-001-S01", readback["source_record"]["text"])
        self.assertFalse(readback["readback_required"])
        self.assertEqual(frames[4]["result"], {})


if __name__ == "__main__":
    unittest.main()
