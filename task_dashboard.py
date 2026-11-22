"""Interactive Task & Activity Dashboard built with Rich and Textual.

This example shows how the two companion libraries work together:
- **Rich** handles styled terminal rendering (inline markup, `Panel`, `Table.grid`,
  and `RenderableType` objects).
- **Textual** provides the interactive TUI framework on top of Rich (an async event
  loop, a widget DOM tree, CSS-like layout via TCSS, reactive state, keyboard
  bindings, and background workers).

Run normally:
    python task_dashboard.py

Run with live CSS reload and debug console support (requires `textual-dev`):
    textual run --dev task_dashboard.py
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import ClassVar

# --- Rich imports (the visual rendering layer) ---
# RenderableType is a typing alias for anything Rich can draw (markup strings,
# Panel, Table, Syntax, Text, etc.).
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table

# --- Textual imports (the interactive TUI application layer) ---
# `on` binds message handlers using CSS selectors; `work` runs background tasks
# without freezing the UI.
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Footer, Header, Input, RichLog, Static


# ---------------------------------------------------------------------------
# Custom Widget: Combining Textual Reactivity with Rich Renderables
# ---------------------------------------------------------------------------
# Subclass `Static` when creating a custom widget whose job is to render text
# or a Rich renderable (such as a Panel, Table, or Syntax block).
class SummaryCard(Static):
    """Custom widget that renders a Rich Panel + Table from reactive state."""

    # Textual `reactive` descriptors automatically schedule a repaint (calling
    # `render()`) whenever their values change—no manual `refresh()` needed.
    # You can also add `validate_<name>` or `watch_<name>` methods for
    # validation or side effects.
    total: reactive[int] = reactive(0)
    completed: reactive[int] = reactive(0)

    def render(self) -> Panel:
        """Build and return a Rich renderable whenever reactive state changes.

        Returning a Rich object directly from `render()` is one of the cleanest
        ways to embed Rich visuals inside a Textual layout.
        """
        pending = self.total - self.completed

        # `Table.grid()` creates a borderless, headerless Rich Table—ideal for
        # neatly aligning key/value pairs inside a Panel.
        # `expand=True` stretches the grid to fill the widget's available width;
        # `padding=(0, 1)` adds 0 vertical and 1 horizontal cell of spacing.
        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column(style="bold")
        grid.add_column(justify="right")

        # Rich Console Markup uses BBCode-like tags (`[cyan]...[/]`). The bare
        # `[/]` closing tag automatically closes the most recently opened style.
        grid.add_row("Total Tasks", f"[cyan]{self.total}[/]")
        grid.add_row("Completed", f"[green]{self.completed}[/]")
        grid.add_row("Pending", f"[yellow]{pending}[/]")

        # Wrap the grid in a Rich Panel with a title and colored border.
        return Panel(grid, title="Overview", border_style="cyan")


# ---------------------------------------------------------------------------
# Main Application: Layout (TCSS), Widgets (DOM), Events, and Async Workers
# ---------------------------------------------------------------------------
class TaskDashboard(App):
    # `TITLE` and `SUB_TITLE` are automatically displayed by the `Header` widget.
    # They are reactive attributes on `App`, so changing `self.sub_title` at
    # runtime updates the header immediately.
    TITLE = "Task & Activity Dashboard"
    SUB_TITLE = "Rich + Textual Demo"

    # Textual CSS (TCSS) separates layout and visual styling from Python logic.
    # For larger apps, move this into a `styles.tcss` file and set
    # `CSS_PATH = "styles.tcss"` so `textual run --dev` can hot-reload changes.
    CSS = """
    /* The root Screen stacks its direct children vertically by default. */
    Screen {
        layout: vertical;
    }

    /* `#id` selects a widget by its `id="..."` attribute.
       `height: auto` sizes the bar to fit its children.
       `$panel` and `$primary` are built-in theme variables that adapt
       automatically when the user switches themes. */
    #top-bar {
        height: auto;
        padding: 1 2; /* 1 cell top/bottom, 2 cells left/right */
        background: $panel;
        border-bottom: solid $primary;
    }

    /* Fractional units (`1fr`) claim all remaining space not used by siblings,
       so the Input stretches while the Buttons stay at their natural width. */
    #task-input {
        width: 1fr;
        margin-right: 1;
    }

    /* `height: 1fr` fills the vertical space between `#top-bar` and `Footer`. */
    #body {
        height: 1fr;
        padding: 1 2;
    }

    /* `2fr` vs `1fr` creates a responsive 2:1 split across the terminal width. */
    #left-pane {
        width: 2fr;
        margin-right: 1;
    }

    #right-pane {
        width: 1fr;
    }

    /* Type selectors target every instance of a widget class.
       `border: round $primary` draws rounded Unicode box-drawing corners. */
    DataTable {
        height: 1fr;
        border: round $primary;
    }

    SummaryCard {
        height: auto;
        margin-bottom: 1;
    }

    RichLog {
        height: 1fr;
        border: round $accent;
        background: $surface;
        padding: 0 1;
    }
    """

    # `BINDINGS` maps keys to `action_<name>` methods on this class and
    # automatically displays them in the `Footer` bar and Command Palette (Ctrl+P).
    # Annotate with `ClassVar[list[BindingType]]` to match `App.BINDINGS` and
    # satisfy linters (e.g. Ruff RUF012) and type checkers.
    # Note: `"quit"` calls Textual's built-in `App.action_quit()`.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("space", "toggle_task", "Toggle Done"),
        Binding("s", "sync_tasks", "Sync"),
        Binding("t", "toggle_theme", "Theme"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        # Keep application state separate from widgets; widgets act as views.
        # Note: The widget DOM does not exist yet in `__init__`, so never call
        # `query_one()` here—do widget initialization in `on_mount()` instead.
        self._tasks: dict[str, dict[str, str | bool]] = {}
        self._next_id = 1

    def compose(self) -> ComposeResult:
        """Build the initial Widget Tree (DOM) by yielding widgets.

        Use container context managers (`with Horizontal():`, `with Vertical():`)
        to nest child widgets inside layout containers.
        """
        # `Header` and `Footer` dock themselves to the top and bottom edges.
        yield Header(show_clock=True)

        # Horizontal arranges its yielded children side-by-side (left to right).
        with Horizontal(id="top-bar"):
            yield Input(placeholder="Add a new task and press Enter...", id="task-input")
            # `variant` applies semantic theme styling (primary, success, warning, error).
            yield Button("Add Task", variant="primary", id="add-btn")
            yield Button("Sync", variant="success", id="sync-btn")

        with Horizontal(id="body"):
            with Vertical(id="left-pane"):
                # Use Textual's `DataTable` (instead of a Rich `Table`) whenever
                # you need scrolling, keyboard focus, or row/cell selection.
                # `cursor_type="row"` highlights the entire row under the cursor.
                yield DataTable(cursor_type="row", id="task-table")
            with Vertical(id="right-pane"):
                yield SummaryCard(id="summary")
                # `RichLog` is a scrollable viewport for Rich output:
                # - `markup=True` parses Rich tags like `[bold cyan]...[/]`
                # - `highlight=True` auto-styles numbers, paths, and keywords
                yield RichLog(markup=True, highlight=True, id="activity-log")

        yield Footer()

    def on_mount(self) -> None:
        """Lifecycle hook run once all composed widgets are mounted in the DOM."""
        # `query_one(selector, WidgetType)` looks up a single widget via CSS
        # selector and verifies its type for both runtime safety and type checkers.
        table = self.query_one("#task-table", DataTable)

        # Giving each column a stable `key` lets us update cells by name
        # (e.g. `"status"`) instead of relying on fragile numeric indexes.
        table.add_column("ID", key="id")
        table.add_column("Task", key="task")
        table.add_column("Status", key="status")

        self._add_task("Design TCSS layout")
        self._add_task("Embed Rich summary card")
        self._add_task("Write pytest Pilot tests")
        self._log("[bold cyan]Dashboard ready.[/] Press [bold]Space[/] to toggle a task.")

    def _log(self, message: RenderableType) -> None:
        """Write either a Rich markup string or any Rich renderable to RichLog.

        Never call `print()` inside a Textual app—Textual owns the terminal
        screen. Use a `RichLog` widget for user-facing logs, or `self.log(...)`
        to stream debug messages to `textual console`.
        """
        rich_log = self.query_one("#activity-log", RichLog)
        if isinstance(message, str):
            ts = datetime.now().strftime("%H:%M:%S")
            rich_log.write(f"[dim]{ts}[/] {message}")
        else:
            # RichLog accepts full Rich renderables like Panel, Table, or Syntax.
            rich_log.write(message)

    def _refresh_summary(self) -> None:
        """Update SummaryCard's reactive attributes to trigger an automatic repaint."""
        summary = self.query_one("#summary", SummaryCard)
        summary.total = len(self._tasks)
        summary.completed = sum(1 for t in self._tasks.values() if t["done"])

    def _add_task(self, title: str) -> None:
        row_key = f"T-{self._next_id:02d}"
        self._next_id += 1
        self._tasks[row_key] = {"title": title, "done": False}

        table = self.query_one("#task-table", DataTable)
        # Passing `key=row_key` associates the row with a stable identifier so
        # we can update it later even if rows are sorted or removed.
        # DataTable cells natively render Rich markup strings like `[yellow]`.
        table.add_row(row_key, title, "[yellow]Pending[/]", key=row_key)
        self._refresh_summary()
        self._log(f"Added [bold]{row_key}[/]: {title}")

    # Textual widgets communicate by posting Message objects up the DOM tree.
    # `@on(MessageClass, "css-selector")` routes matching messages to a method,
    # and decorators can be stacked so clicking the button OR pressing Enter
    # inside the Input runs the exact same handler.
    @on(Button.Pressed, "#add-btn")
    @on(Input.Submitted, "#task-input")
    def handle_add_task(self) -> None:
        # The event parameter is optional when the handler doesn't need it.
        inp = self.query_one("#task-input", Input)
        if title := inp.value.strip():
            self._add_task(title)
            inp.value = ""

    @on(Button.Pressed, "#sync-btn")
    def handle_sync_button(self) -> None:
        # Delegate to the action method so the button and `s` shortcut share one path.
        self.action_sync_tasks()

    # Action methods are named `action_<binding_action>` and invoked by BINDINGS.
    def action_toggle_task(self) -> None:
        table = self.query_one("#task-table", DataTable)
        if table.row_count == 0:
            return

        # Convert the cursor's visual (row, col) coordinate into our stable
        # RowKey so lookups stay accurate even if rows are reordered or deleted.
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        key_str = str(row_key.value)
        task = self._tasks[key_str]
        task["done"] = not task["done"]

        status = "[bold green]Done[/]" if task["done"] else "[yellow]Pending[/]"
        # Update a single cell in place by (row_key, column_key) instead of
        # clearing and rebuilding the entire table.
        table.update_cell(row_key, "status", status)
        self._refresh_summary()
        self._log(f"Marked [bold]{key_str}[/] as {status}")

    # `@work` runs slow/async operations as a managed Textual Worker so the UI
    # stays responsive (never call blocking `time.sleep()` or `requests.get()`
    # on the event loop; for blocking libraries use `@work(thread=True)` and
    # marshal UI updates back with `self.call_from_thread(...)`).
    # `exclusive=True` automatically cancels any previous in-flight sync if
    # triggered again before finishing.
    @work(exclusive=True)
    async def action_sync_tasks(self) -> None:
        self._log("[italic]Syncing with remote...[/]")
        await asyncio.sleep(1.0)
        # `self.notify()` shows a built-in non-blocking toast notification.
        self.notify("Tasks synced!", title="Sync Complete")
        # RichLog can display rich structured components like a Rich Panel.
        self._log(Panel("Remote state is up to date.", border_style="green"))

    def action_toggle_theme(self) -> None:
        # Changing `self.theme` re-evaluates all TCSS `$variable` colors live.
        # Users can also pick any built-in theme via the Command Palette (Ctrl+P).
        self.theme = (
            "textual-light" if self.theme == "textual-dark" else "textual-dark"
        )


if __name__ == "__main__":
    # `.run()` enters Textual's async event loop, switches to the terminal's
    # alternate screen buffer, enables mouse/keyboard events, and restores the
    # terminal cleanly when the app exits.
    TaskDashboard().run()
