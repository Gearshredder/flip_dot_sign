"""Desktop simulator for the flip-dot sign using Tkinter.

The simulator renders the sign buffer maintained by ``Display``
onto a simple grid of rectangles. It reuses the font loading logic
from ``main.py`` so rendered characters match the hardware.
"""
import json
import tkinter as tk
from tkinter import ttk

from lib.flipper import Display


def load_font(path: str = "font1.json") -> list:
    """Load the 5x7 font table from ``font1.json``.

    Returns a list indexed by ASCII value where each entry contains seven
    row bytes describing a 5x7 character.
    """
    with open(path, "r", encoding="utf-8") as font_file:
        ascii_dict = json.load(font_file)
        return [ascii_dict[char][1:8] for char in range(123)]


class FlipDotSimulator:
    """Tkinter-based flip-dot sign simulator."""

    def __init__(self, modules: int = 3, cell_size: int = 24) -> None:
        self.font = load_font()
        self.cell_size = cell_size
        self.modules = modules
        self.column_gap_cells = 1  # blank column after every 5 columns for readability
        self.sign = Display(modules)
        self.sign.fill(0)

        self.processing_overhead_ms = 1
        self.flip_delay_ms = self.sign.flip_ms + self.processing_overhead_ms

        self.root = tk.Tk()
        self.root.title("Flip-Dot Sign Simulator")

        self._build_controls()
        self._build_canvas()
        self._draw_cells()

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

        total_width = self._canvas_width
        total_height = self.cell_size * 7
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
        return self.modules * 5

    @property
    def _canvas_width(self) -> int:
        visual_columns = self._columns + (self.modules - 1) * self.column_gap_cells
        return self.cell_size * visual_columns

    # Actions ------------------------------------------------------------
    def _on_modules_changed(self) -> None:
        self.modules = int(self.modules_var.get())
        self.sign.modules = self.modules
        self._fill(0)
        self._resize_canvas()
        self.render_text()

    def _resize_canvas(self) -> None:
        self.canvas.configure(width=self._canvas_width)
        self._draw_cells()

    def _fill(self, color: int) -> None:
        self.sign.fill(color)
        self._refresh_grid()

    def render_text(self) -> None:
        self._fill(0)
        text = self.text_var.get()
        trimmed = text[: self.modules]
        self.sign.write_string_to_buffer(trimmed, self.font)
        self._refresh_grid()

    def _refresh_grid(self) -> None:
        changes: list[tuple[int, int, bool]] = []
        for row in range(7):
            row_value = self.sign.display_buffer1[row]
            for col in range(self._columns):
                is_on = bool(row_value & (1 << (col)))
                if is_on != self.current_states[row][col]:
                    changes.append((row, col, is_on))

        for index, (row, col, is_on) in enumerate(changes):
            delay = index * self.flip_delay_ms
            self.root.after(delay, self._apply_cell_state, row, col, is_on)

    def _apply_cell_state(self, row: int, col: int, is_on: bool) -> None:
        color = "gold" if is_on else "gray20"
        self.canvas.itemconfigure(self.cell_ids[row][col], fill=color)
        self.current_states[row][col] = is_on

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    simulator = FlipDotSimulator()
    simulator.run()


if __name__ == "__main__":
    main()
