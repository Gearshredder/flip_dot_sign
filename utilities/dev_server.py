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

    MAX_CHARS = 15

    def __init__(self, simulator: FlipDotSimulator) -> None:
        self.simulator = simulator
        self.mode = "text"
        self.current_text = ""
        self.scroll_lines: list[str] = []
        self.scroll_index = 0
        self.scroll_interval = 2.5
        self.countdown_target: float | None = None
        self.scroll_presets: dict[str, list[str]] = {
            "commute": ["NEXT STOP", "CITY CENTER", "TRANSFER AHEAD"],
            "alerts": ["WELCOME ABOARD", "CHECK SIGNAL", "SEE DISPATCH"],
            "festive": ["HAPPY HOLIDAYS", "SNOW ROUTE", "STAY WARM!"],
        }
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def set_text_mode(self, text: str) -> None:
        self.mode = "text"
        self.scroll_lines = []
        cleaned = self._sanitize_text(text, strip=False)
        if cleaned:
            self.current_text = cleaned
            self.simulator.queue_text(cleaned)

    def set_time_mode(self) -> None:
        self.mode = "time"
        self.scroll_lines = []
        self.countdown_target = None

    def set_manual_time(self, time_string: str) -> None:
        cleaned = time_string.rstrip()
        if not cleaned:
            return
        if len(cleaned) == 5:
            cleaned = f"{cleaned}:00"
        cleaned = self._sanitize_text(cleaned, preserve_colon=True)
        self.mode = "manual_time"
        self.scroll_lines = []
        self.current_text = cleaned
        self.simulator.queue_text(cleaned)

    def set_scroll_mode(self, lines: list[str], interval: float = 2.5) -> None:
        self.mode = "scroll"
        processed = [
            self._sanitize_text(line, strip=False) for line in lines if line.rstrip("\n")
        ]
        if len(processed) == 1:
            self.set_text_mode(processed[0])
            return
        self.scroll_lines = processed or ["SCROLL"]
        self.scroll_index = 0
        self.current_text = ""
        self.scroll_interval = max(0.5, min(10.0, interval))

    def set_scroll_preset(self, preset_key: str, interval: float = 2.5) -> None:
        lines = self.scroll_presets.get(preset_key.lower())
        if lines:
            self.set_scroll_mode(lines, interval)

    def set_countdown(self, minutes: int) -> None:
        clamped = max(1, min(180, minutes))
        self.mode = "countdown"
        self.scroll_lines = []
        self.countdown_target = time.time() + clamped * 60
        self._display_countdown(force=True)

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=1)

    def fill_on(self) -> None:
        self.simulator.fill_on()

    def fill_off(self) -> None:
        self.simulator.fill_off()

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
            elif self.mode == "countdown":
                if not self._display_countdown():
                    time.sleep(0.25)
                else:
                    time.sleep(1)
            elif self.mode == "manual_time":
                time.sleep(0.25)
            else:
                time.sleep(0.1)

    def _display_countdown(self, force: bool = False) -> bool:
        if not self.countdown_target:
            return False
        remaining = max(0, int(self.countdown_target - time.time()))
        minutes, seconds = divmod(remaining, 60)
        text = f"{minutes:02d}:{seconds:02d}"
        if remaining == 0:
            self.mode = "manual_time"
            text = "TIME UP!"
            self.countdown_target = None
            sanitized = self._sanitize_text(text, force_upper=True)
        else:
            sanitized = self._sanitize_text(text, preserve_colon=True)
        if force or sanitized != self.current_text:
            self.current_text = sanitized
            self.simulator.queue_text(sanitized)
        return remaining > 0

    def _sanitize_text(
        self,
        value: str,
        preserve_colon: bool = False,
        force_upper: bool = False,
        strip: bool = True,
    ) -> str:
        if not value:
            return ""
        cleaned = value.rstrip("\n")
        if strip:
            cleaned = cleaned.strip()
        if preserve_colon:
            allowed = "0123456789: "
            cleaned = "".join(ch for ch in cleaned if ch in allowed)
        if force_upper:
            cleaned = cleaned.upper()
        return cleaned[: self.MAX_CHARS]


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
            action = params.get("action", [""])[0]
            if action == "text":
                entry = params.get("entry", [""])[0]
                controller.set_text_mode(entry)
            elif action == "scroll":
                scroll_text = params.get("scroll_text", [""])[0]
                interval = 2.5
                interval_value = params.get("scroll_interval", [""])[0]
                if interval_value:
                    try:
                        interval = float(interval_value)
                    except ValueError:
                        interval = 2.5
                controller.set_scroll_mode(scroll_text.splitlines(), interval)
            elif action == "scroll_preset":
                preset = params.get("preset", [""])[0]
                interval = 2.5
                interval_value = params.get("scroll_interval", [""])[0]
                if interval_value:
                    try:
                        interval = float(interval_value)
                    except ValueError:
                        interval = 2.5
                controller.set_scroll_preset(preset, interval)
            elif action == "time_auto":
                controller.set_time_mode()
            elif action == "time_manual":
                manual_time = params.get("manual_time", [""])[0]
                controller.set_manual_time(manual_time)
            elif action == "countdown":
                minutes_value = params.get("countdown_minutes", [""])[0]
                try:
                    minutes = int(minutes_value)
                except ValueError:
                    minutes = 1
                controller.set_countdown(minutes)
            elif action == "fill_on":
                controller.fill_on()
            elif action == "fill_off":
                controller.fill_off()
            else:
                # Backwards compatibility with legacy query parameters
                mode = params.get("mode", [""])[0]
                if mode == "time":
                    controller.set_time_mode()
                elif mode == "scroll":
                    scroll_text = params.get("scroll_text", [""])[0]
                    controller.set_scroll_mode(scroll_text.splitlines())
                elif mode:
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
