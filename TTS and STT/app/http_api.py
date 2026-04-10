from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from .agent import IndianVoiceAgent
from .models import ChatRequest


class VoiceAgentHandler(BaseHTTPRequestHandler):
    agent = IndianVoiceAgent()

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            raise ValueError("Request body is empty")
        raw = self.rfile.read(length)
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._write_json(
                HTTPStatus.OK,
                {"status": "ok", "service": "indian-voice-agent"},
            )
            return

        if parsed.path == "/metadata":
            self._write_json(HTTPStatus.OK, self.agent.metadata())
            return

        self._write_json(HTTPStatus.NOT_FOUND, {"error": "Route not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/chat":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "Route not found"})
            return

        try:
            payload = self._read_json()
            chat_request = ChatRequest.from_dict(payload)
            chat_response = self.agent.respond(
                message=chat_request.message,
                history=chat_request.history,
            )
        except json.JSONDecodeError:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON payload"})
            return
        except ValueError as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception as exc:  # pragma: no cover
            self._write_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": f"Unexpected error: {exc}"},
            )
            return

        self._write_json(HTTPStatus.OK, chat_response.to_dict())

    def log_message(self, format: str, *args: object) -> None:
        # Keep output concise for API mode.
        return


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), VoiceAgentHandler)
    print(f"Voice agent API is running on http://{host}:{port}")
    print("Available endpoints: GET /health, GET /metadata, POST /chat")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Server stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Indian Voice Agent HTTP API")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
