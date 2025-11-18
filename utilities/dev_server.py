import argparse
import sys
import threading
import time
import urllib.parse
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from lib.web_template import HTML_PAGE
from utilities.simulator import FlipDotSimulator

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080


class SimulatorController:
    """Background helper that keeps the simulator in sync with selected modes."""

    def __init__(self, simulator: FlipDotSimulator) -> None:
        self.simulator = simulator
        self.mode = "text"
        self.current_text = ""
        self.scroll_lines: list[str] = []
        self.scroll_index = 0
        self.scroll_interval = 2.5
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def set_text_mode(self, text: str) -> None:
        self.mode = "text"
        self.scroll_lines = []
        cleaned = text.strip().upper()
        if cleaned:
            self.current_text = cleaned
            self.simulator.queue_text(cleaned)

    def set_time_mode(self) -> None:
        self.mode = "time"
        self.scroll_lines = []

    def set_scroll_mode(self, lines: list[str]) -> None:
        self.mode = "scroll"
        processed = [line.strip().upper() for line in lines if line.strip()]
        self.scroll_lines = processed or ["SCROLL"]
        self.scroll_index = 0
        self.current_text = ""

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=1)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            if self.mode == "time":
                timestamp = datetime.now().strftime("%H:%M:%S")
                if timestamp != self.current_text:
                    self.current_text = timestamp
                    self.simulator.queue_text(timestamp)
                time.sleep(0.5)
            elif self.mode == "scroll":
                if self.scroll_lines:
                    next_text = self.scroll_lines[self.scroll_index]
                    self.scroll_index = (self.scroll_index + 1) % len(self.scroll_lines)
                    if next_text != self.current_text:
                        self.current_text = next_text
                        self.simulator.queue_text(next_text)
                time.sleep(self.scroll_interval)
            else:
                time.sleep(0.1)


def build_handler(controller: SimulatorController):
    class SignRequestHandler(BaseHTTPRequestHandler):
        server_version = "FlipDotDevServer/1.1"

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path not in ("/", ""):
                self.send_error(404, "Not Found")
                return

            params = urllib.parse.parse_qs(parsed.query)
            self._handle_mode(params)
            self._write_html_response(HTML_PAGE)

        def log_message(self, format, *args):
            sys.stdout.write("[HTTP] %s - - %s\n" % (self.address_string(), format % args))

        def _handle_mode(self, params: dict[str, list[str]]) -> None:
            mode = params.get("mode", ["text"])[0]
            if mode == "time":
                controller.set_time_mode()
            elif mode == "scroll":
                scroll_text = params.get("scroll_text", [""])[0]
                controller.set_scroll_mode(scroll_text.splitlines())
            else:
                entry = params.get("entry", [""])[0]
                controller.set_text_mode(entry)

        def _write_html_response(self, html: str) -> None:
            payload = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

    return SignRequestHandler


def start_server(controller: SimulatorController, host: str, port: int) -> ThreadingHTTPServer:
    handler_cls = build_handler(controller)
    server = ThreadingHTTPServer((host, port), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the Tk simulator alongside a local preview of the Flip-Dot web UI."
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host/IP to bind the preview server.")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Port for the preview server (default: 8080)."
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the browser after starting the server.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    simulator = FlipDotSimulator()
    controller = SimulatorController(simulator)
    server = start_server(controller, args.host, args.port)
    url = f"http://{args.host}:{args.port}/"
    print(f"Web preview available at {url}")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        simulator.run()
    finally:
        controller.stop()
        server.shutdown()


if __name__ == "__main__":
    main()
