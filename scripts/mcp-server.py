#!/usr/bin/env python3
"""Read-only MCP stdio server, pinned to the 2025-11-25 handshake protocol.

Protocol references:
https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle
https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
https://modelcontextprotocol.io/specification/2025-11-25/server/tools

Only UTF-8 newline-delimited JSON-RPC messages go to stdout. No HTTP server,
external command execution, arbitrary-path tool, or network access is provided.
"""

import json
import re
import sys

sys.dont_write_bytecode = True
from library import InputError, Library, LibraryError, REPOSITORY_URL, VERSION, reject_constant


SUPPORTED_PROTOCOLS = ("2025-11-25", "2025-06-18")
MAX_REQUEST_BYTES = 64 * 1024
INSTRUCTIONS = (
    "This is a read-only research-preview mechanism library. Gold/Silver/Reference are internal judgments. "
    "Use search_archetypes for recall, get_archetype to read full cards and source records, and read_rules before adaptation. "
    "Keep FACT, INTERPRETATION and ADAPTATION separate. Never eroticize age-unknown/minor originals; H4 is a separate explicit-adult design. "
    "Do not copy original plot sequences or treat source-link existence as fact verification. "
    "Original project content is CC-BY-4.0 and original code is MIT; third-party works, translations and quotations are excluded. "
    "Attribute original content to jsfgmkg95d-source / Urban Desire Female Archetypes; license scope is at "
    + REPOSITORY_URL + "/blob/main/COPYRIGHT.md."
)


class ProtocolError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def error_response(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def valid_id(value):
    return type(value) is int or (isinstance(value, str) and 0 < len(value) <= 1024)


def parameters(params, allowed, required=()):
    if not isinstance(params, dict):
        raise ProtocolError(-32602, "params must be an object")
    if "_meta" in params and not isinstance(params["_meta"], dict):
        raise ProtocolError(-32602, "_meta must be an object")
    extra = params.keys() - set(allowed) - {"_meta"}
    missing = set(required) - params.keys()
    if extra or missing:
        raise ProtocolError(-32602, f"Parameter mismatch: unknown={sorted(extra)}, missing={sorted(missing)}")
    return params


class Server:
    def __init__(self, library=None):
        self.library = library if library is not None else Library()
        self.phase = "new"
        self.protocol_version = None

    def handle(self, message):
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return error_response(None, -32600, "Expected one JSON-RPC 2.0 object; batches are unsupported")
        # Responses are not requests, and this tools-only server never initiates requests.
        if "method" not in message and "id" in message and ("result" in message or "error" in message):
            return None
        if not isinstance(message.get("method"), str) or not message["method"]:
            return error_response(None, -32600, "method must be a nonempty string")
        method = message["method"]
        if "id" not in message:
            # Notifications, including unsupported/cancellation notifications, get no response.
            if method == "notifications/initialized" and self.phase == "negotiated":
                self.phase = "ready"
            return None
        request_id = message["id"]
        if not valid_id(request_id):
            return error_response(None, -32600, "Request ID must be a string or integer, never null or boolean")
        try:
            result = self.dispatch(method, message.get("params", {}))
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except ProtocolError as error:
            return error_response(request_id, error.code, str(error))
        except (LibraryError, OSError, ValueError, KeyError, TypeError) as error:
            # A local data error is not protocol output, and should not disclose unrelated paths.
            print(f"MCP local data error: {type(error).__name__}", file=sys.stderr)
            return error_response(request_id, -32603, "Local library read failed; run validate-library.py and inspect stderr")

    def dispatch(self, method, params):
        if method == "initialize":
            if self.phase != "new":
                raise ProtocolError(-32600, "Server is already initialized")
            params = parameters(params, ("protocolVersion", "capabilities", "clientInfo"),
                                ("protocolVersion", "capabilities", "clientInfo"))
            version = params["protocolVersion"]
            if not isinstance(version, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", version):
                raise ProtocolError(-32602, "protocolVersion must be a dated MCP revision")
            if not isinstance(params["capabilities"], dict) or not isinstance(params["clientInfo"], dict):
                raise ProtocolError(-32602, "capabilities and clientInfo must be objects")
            for field in ("name", "version"):
                value = params["clientInfo"].get(field)
                if not isinstance(value, str) or not value.strip() or len(value) > 256:
                    raise ProtocolError(-32602, f"clientInfo.{field} must be a nonempty string of at most 256 characters")
            self.protocol_version = version if version in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
            self.phase = "negotiated"
            return {"protocolVersion": self.protocol_version, "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "urban-desire-female-archetypes", "version": VERSION,
                                   "title": "人物机制研究库", "websiteUrl": REPOSITORY_URL},
                    "instructions": INSTRUCTIONS}
        if method == "ping":
            parameters(params, ())
            return {}
        if method not in ("tools/list", "tools/call"):
            raise ProtocolError(-32601, f"Method not found: {method}")
        if self.phase != "ready":
            raise ProtocolError(-32002, "Initialize and send notifications/initialized before using tools")
        if method == "tools/list":
            params = parameters(params, ("cursor",))
            if "cursor" in params:
                raise ProtocolError(-32602, "This small static tool list has no continuation cursor")
            return {"tools": self.library.tool_definitions()}
        params = parameters(params, ("name", "arguments"), ("name",))
        name = params["name"]
        if not isinstance(name, str) or name not in {tool["name"] for tool in self.library.tool_definitions()}:
            raise ProtocolError(-32602, "Unknown tool name")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ProtocolError(-32602, "arguments must be an object")
        try:
            data = self.library.call_tool(name, arguments)
        except InputError as error:
            data = {"quality_status": "research-preview", "error": {"code": "invalid_input", "message": str(error)}}
            return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
                    "structuredContent": data, "isError": True}
        return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
                "structuredContent": data, "isError": False}


def serve(input_stream, output_stream, server):
    def send(response):
        if response is not None:
            raw = json.dumps(response, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
            output_stream.write(raw + b"\n")
            output_stream.flush()

    while True:
        line = input_stream.readline(MAX_REQUEST_BYTES + 1)
        if not line:
            break
        if len(line) > MAX_REQUEST_BYTES:
            while line and not line.endswith(b"\n"):
                line = input_stream.readline(MAX_REQUEST_BYTES + 1)
            send(error_response(None, -32600, "Request exceeds 64 KiB frame limit"))
            continue
        try:
            message = json.loads(line.decode("utf-8"), parse_constant=reject_constant)
        except (ValueError, UnicodeError):
            send(error_response(None, -32700, "Invalid UTF-8 JSON message"))
            continue
        send(server.handle(message))


def main():
    try:
        server = Server()
        serve(sys.stdin.buffer, sys.stdout.buffer, server)
    except (LibraryError, OSError) as error:
        print(f"MCP startup/read error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
