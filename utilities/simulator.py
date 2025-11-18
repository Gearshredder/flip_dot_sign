"""Desktop simulator for the flip-dot sign using Tkinter.

The simulator renders the sign buffer maintained by ``Display``
onto a simple grid of rectangles. It reuses the font loading logic
from ``main.py`` so rendered characters match the hardware.
"""
import json
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from queue import Empty, SimpleQueue

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from lib.flipper import Display


def load_font(path: str | Path = "config/font1.json") -> list:
    """Load the 5x7 font table from ``font1.json``.

    Returns a list indexed by ASCII value where each entry contains seven
    row bytes describing a 5x7 character.
    """
    font_path = Path(path)
    if not font_path.is_absolute():
        project_root = Path(__file__).resolve().parents[1]
        font_path = project_root / font_path

    with open(font_path, "r", encoding="utf-8") as font_file:
        ascii_dict = json.load(font_file)
        return [ascii_dict[char][1:8] for char in range(123)]


class FlipDotSimulator:
    """Tkinter-based flip-dot sign simulator."""

    def __init__(self, modules: int = 3, cell_size: int = 24) -> None:
        self.font = load_font()
        self.base_cell_size = cell_size
        self.cell_size = cell_size
        self.min_cell_size = 4
        self.modules = modules
        self.column_gap_cells = 1  # blank column after every 5 columns for readability
        self.sign = Display(modules)
        self.sign.fill(0)

        self.processing_overhead_ms = 1
        self.flip_delay_ms = self.sign.flip_ms + self.processing_overhead_ms

        self.root = tk.Tk()
        self.root.title("Flip-Dot Sign Simulator")
        self.max_canvas_width = max(600, int(self.root.winfo_screenwidth() * 0.9))

        self._command_queue: SimpleQueue[tuple[str, str]] = SimpleQueue()
        self._update_token = 0

        self._build_controls()
        self._build_canvas()
        self._draw_cells()
        self._poll_command_queue()
        self._boot_animation()

    # UI helpers ---------------------------------------------------------
    def _build_controls(self) -> None:
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(control_frame, text="Message:").grid(row=0, column=0, padx=5, pady=5)
        self.text_var = tk.StringVar(value="HELLO")
        text_entry = ttk.Entry(control_frame, textvariable=self.text_var, width=30)
        text_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(control_frame, text="Modules:").grid(row=0, column=2, padx=5, pady=5)
        self.modules_var = tk.IntVar(value=self.modules)
        modules_spin = ttk.Spinbox(
            control_frame,
            from_=1,
            to=10,
            textvariable=self.modules_var,
            width=5,
            command=self._on_modules_changed,
        )
        modules_spin.grid(row=0, column=3, padx=5, pady=5)

        render_button = ttk.Button(control_frame, text="Render", command=self.render_text)
        render_button.grid(row=0, column=4, padx=5, pady=5)

        fill_on_button = ttk.Button(control_frame, text="Fill On", command=lambda: self._fill(1))
        fill_on_button.grid(row=0, column=5, padx=5, pady=5)

        fill_off_button = ttk.Button(control_frame, text="Fill Off", command=lambda: self._fill(0))
        fill_off_button.grid(row=0, column=6, padx=5, pady=5)

        control_frame.columnconfigure(1, weight=1)

    def _build_canvas(self) -> None:
        self.canvas_frame = ttk.Frame(self.root, padding=10)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._update_cell_size()
        total_width = self._canvas_width
        total_height = self._canvas_height
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=total_width,
            height=total_height,
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack()

    def _draw_cells(self) -> None:
        self.canvas.delete("all")
        self.cell_ids = []
        self.current_states: list[list[bool]] = []
        for row in range(7):
            row_ids = []
            state_row = []
            for col in range(self._columns):
                visual_col = col + col // 5 * self.column_gap_cells
                x1 = visual_col * self.cell_size + 2
                y1 = row * self.cell_size + 2
                x2 = x1 + self.cell_size - 4
                y2 = y1 + self.cell_size - 4
                rect_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="gray20", outline="gray40"
                )
                row_ids.append(rect_id)
                state_row.append(False)
            self.cell_ids.append(row_ids)
            self.current_states.append(state_row)
        self._refresh_grid()

    # Properties ---------------------------------------------------------
    @property
    def _columns(self) -> int:
        # Each module supports 5 characters and every character is 5 columns wide
        return self.modules * 25

    @property
    def _canvas_width(self) -> int:
        return self.cell_size * self._visual_columns

    @property
    def _canvas_height(self) -> int:
        return self.cell_size * 7

    @property
    def _visual_columns(self) -> int:
        if self._columns <= 1 or self.column_gap_cells <= 0:
            return self._columns
        gaps = ((self._columns - 1) // 5) * self.column_gap_cells
        return self._columns + gaps

    # Actions ------------------------------------------------------------
    def _on_modules_changed(self) -> None:
        self.modules = int(self.modules_var.get())
        self.sign.modules = self.modules
        self._resize_canvas()
        self.render_text()

    def _resize_canvas(self) -> None:
        self._update_cell_size()
        self.canvas.configure(width=self._canvas_width, height=self._canvas_height)
        self._draw_cells()

    def _fill(self, color: int) -> None:
        self.sign.fill(color)
        self._refresh_grid()

    def render_text(self) -> None:
        self.display_text(self.text_var.get())

    def display_text(self, text: str) -> None:
        self.text_var.set(text)
        self._apply_text_to_buffer(text)

    def queue_text(self, text: str) -> None:
        self._command_queue.put(("text", text))

    def _apply_text_to_buffer(self, text: str) -> None:
        self._fill(0)
        trimmed = text[: self.modules * 5]
        self.sign.write_string_to_buffer(trimmed, self.font)
        self._refresh_grid()

    def _refresh_grid(self) -> None:
        self._update_token += 1
        token = self._update_token
        changes: list[tuple[int, int, bool]] = []
        for row in range(7):
            row_value = self.sign.display_buffer1[row]
            for col in range(self._columns):
                is_on = bool(row_value & (1 << (col)))
                if is_on != self.current_states[row][col]:
                    changes.append((row, col, is_on))

        for index, (row, col, is_on) in enumerate(changes):
            delay = index * self.flip_delay_ms
            self.root.after(delay, self._apply_cell_state, row, col, is_on, token)

    def _apply_cell_state(self, row: int, col: int, is_on: bool, token: int) -> None:
        if token != self._update_token:
            return
        color = "gold" if is_on else "gray20"
        self.canvas.itemconfigure(self.cell_ids[row][col], fill=color)
        self.current_states[row][col] = is_on

    def _poll_command_queue(self) -> None:
        try:
            while True:
                command, payload = self._command_queue.get_nowait()
                if command == "text":
                    self.display_text(payload)
        except Empty:
            pass
        finally:
            self.root.after(50, self._poll_command_queue)

    def _update_cell_size(self) -> None:
        if self._visual_columns == 0:
            return
        available_size = self.max_canvas_width // self._visual_columns
        if available_size <= 0:
            available_size = self.min_cell_size
        new_size = max(self.min_cell_size, min(self.base_cell_size, available_size))
        if new_size != self.cell_size:
            self.cell_size = new_size

    def _boot_animation(self) -> None:
        # Mimic the ESP32 boot sequence: fill on, then clear after all flips.
        self._fill(1)
        total_cells = max(1, self._columns * 7)
        boot_duration = max(600, total_cells * self.flip_delay_ms)
        self.root.after(boot_duration, lambda: self._fill(0))

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    simulator = FlipDotSimulator()
    simulator.run()


if __name__ == "__main__":
    main()
