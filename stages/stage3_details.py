"""Stage 3: Display Read-Only Details for the Selected Item (Master-Detail).

Builds on Stage 2 by splitting ``#workspace`` into two panes: the filterable
item list on the left and a read-only Rich detail view on the right that
updates automatically whenever another item is selected.

New concepts introduced in Stage 3:
- Master-detail TCSS layout (``#list-pane`` 1fr vs ``#detail-pane`` 2fr)
- Tracking selection with a Textual ``reactive[int | None]`` attribute and
  ``watch_current_index()`` watcher method
- Handling ``OptionList.OptionHighlighted`` to sync list selection with details
- Rendering structured read-only details using Rich ``Table.grid``, ``Panel``,
  and ``Pretty`` inside Textual ``Static`` widgets
- Graceful empty-state rendering when the filter matches zero items

Run with:
    python stages/stage3_details.py
"""

from __future__ import annotations

from typing import ClassVar

from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, OptionList, Static

FormValue = str | int | float | bool
FormRecord = dict[str, FormValue]

DEFAULT_RECORDS: list[FormRecord] = [
    {
        "username": "ada_lovelace",
        "email": "ada@example.com",
        "port": 8080,
        "timeout_sec": 3.5,
        "auto_save": True,
        "notifications": False,
    },
    {
        "username": "grace_hopper",
        "email": "grace@example.com",
        "port": 9000,
        "timeout_sec": 5.0,
        "auto_save": True,
        "notifications": True,
    },
    {
        "username": "alan_turing",
        "email": "alan@example.com",
        "port": 8443,
        "timeout_sec": 2.0,
        "auto_save": False,
        "notifications": True,
    },
]


class Stage3DetailsApp(App[None]):
    """Stage 3 master-detail app displaying read-only details for selected items.

    Subclasses ``textual.app.App[None]``, where the generic type argument
    (``None``) specifies the return type of ``App.run()``.

    Args:
        initial_records: Non-empty list of flat dictionaries mapping field
            names (``str``) to scalar values (``str | int | float | bool``).
            Copied internally so caller data is never mutated.

    Raises:
        ValueError: If ``initial_records`` is empty.

    Attributes:
        TITLE: Application title displayed in the ``Header`` widget.
        SUB_TITLE: Subtitle displayed next to ``TITLE`` in the ``Header``.
        CSS_PATH: External TCSS stylesheet loaded relative to this file.
        BINDINGS: Keyboard shortcuts displayed in ``Footer`` and the Command
            Palette.
        current_index: Reactive index into ``self._records`` for the currently
            selected item, or ``None`` when the active filter has no matches.
    """

    TITLE = "Stage 3: Item Details"
    SUB_TITLE = "Master-detail view with Rich Panel, Table & Pretty"
    CSS_PATH = "stage3_details.tcss"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+f", "focus_filter", "Filter"),
        Binding("q", "quit", "Quit"),
    ]

    # NEW in Stage 3: reactive selection index (`None` when 0 filter matches).
    current_index: reactive[int | None] = reactive(0, init=False)

    def __init__(self, initial_records: list[FormRecord]) -> None:
        """Initialize the app with copies of ``initial_records``.

        Args:
            initial_records: Non-empty list of dictionaries to display.

        Raises:
            ValueError: If ``initial_records`` is empty.
        """
        if not initial_records:
            raise ValueError("initial_records must contain at least one dictionary.")
        super().__init__()
        self._records: list[FormRecord] = [dict(rec) for rec in initial_records]
        self._filtered_indices: list[int] = list(range(len(self._records)))

    def _record_label(self, index: int, record: FormRecord) -> str:
        """Build a readable label for one dictionary row in ``OptionList``.

        Args:
            index: Zero-based position of ``record`` in ``self._records``.
            record: Dictionary whose first value serves as the display summary.

        Returns:
            Formatted label string like ``"1. ada_lovelace"``.
        """
        summary = next(iter(record.values()), f"Record {index + 1}")
        return f"{index + 1}. {summary}"

    def _format_value(self, value: FormValue) -> str:
        """Format a scalar dictionary value with Rich markup for display.

        Args:
            value: Scalar field value (``bool``, ``int``, ``float``, or ``str``).

        Returns:
            Rich-markup string styled according to the value's Python type.
        """
        if isinstance(value, bool):
            return "[bold green]True[/]" if value else "[bold red]False[/]"
        if isinstance(value, (int, float)):
            return f"[cyan]{value}[/]"
        return str(value)

    def compose(self) -> ComposeResult:
        """Build the top filter bar and two-pane master-detail workspace.

        Yields:
            Top-level widgets (``Header``, filter bar, master/detail panes,
            and ``Footer``).
        """
        yield Header()

        with Horizontal(id="filter-bar"):
            yield Input(
                placeholder="Filter items by any value (Ctrl+F)...",
                id="filter-input",
            )

        # NEW in Stage 3: horizontal split with list on left, details on right.
        with Horizontal(id="workspace"):
            with Vertical(id="list-pane"):
                labels = [
                    self._record_label(i, rec) for i, rec in enumerate(self._records)
                ]
                option_list = OptionList(*labels, id="record-list")
                option_list.border_title = f"Items ({len(self._records)})"
                yield option_list

            with VerticalScroll(id="detail-pane"):
                yield Static(id="detail-card")
                yield Static(id="raw-preview")

        yield Footer()

    def on_mount(self) -> None:
        """Select the first item, focus the list, and render initial details."""
        option_list = self.query_one("#record-list", OptionList)
        option_list.highlighted = 0
        option_list.focus()
        self._render_details()

    def watch_current_index(self, index: int | None) -> None:
        """Re-render the detail pane whenever ``self.current_index`` changes.

        Args:
            index: New index into ``self._records``, or ``None`` when the
                active filter matches zero items.
        """
        _ = index  # Used via self.current_index inside _render_details().
        self._render_details()

    def _render_details(self) -> None:
        """Render the selected item's fields and raw dict using Rich widgets."""
        detail_card = self.query_one("#detail-card", Static)
        raw_preview = self.query_one("#raw-preview", Static)

        if self.current_index is None:
            detail_card.update(
                Panel(
                    "[italic dim]No items match the current filter.[/]",
                    title="Item Details",
                    border_style="yellow",
                )
            )
            raw_preview.update("")
            return

        idx = self.current_index
        record = self._records[idx]

        # Build a borderless Rich grid aligning Field, Value, and Python type.
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column("Field", style="bold")
        grid.add_column("Value")
        grid.add_column("Type", justify="right", style="dim")

        for key, value in record.items():
            label = key.replace("_", " ").title()
            grid.add_row(label, self._format_value(value), type(value).__name__)

        detail_card.update(
            Panel(
                grid,
                title=f"Item #{idx + 1} Details",
                border_style="cyan",
            )
        )
        raw_preview.update(
            Panel(
                Pretty(record),
                title="Raw Dictionary",
                border_style="bright_blue",
            )
        )

    def _apply_filter(self, query: str) -> None:
        """Filter ``#record-list`` and keep ``current_index`` in sync.

        Args:
            query: Case-insensitive search text from ``#filter-input``. An
                empty or whitespace-only string restores all records.
        """
        needle = query.strip().lower()
        self._filtered_indices = [
            i
            for i, rec in enumerate(self._records)
            if not needle or any(needle in str(v).lower() for v in rec.values())
        ]

        option_list = self.query_one("#record-list", OptionList)
        option_list.clear_options()
        option_list.add_options(
            [self._record_label(i, self._records[i]) for i in self._filtered_indices]
        )

        total = len(self._records)
        shown = len(self._filtered_indices)
        option_list.border_title = (
            f"Items ({shown}/{total})" if needle else f"Items ({total})"
        )

        if not self._filtered_indices:
            self.current_index = None
            return

        if self.current_index in self._filtered_indices:
            option_list.highlighted = self._filtered_indices.index(self.current_index)
        else:
            self.current_index = self._filtered_indices[0]
            option_list.highlighted = 0

    @on(Input.Changed, "#filter-input")
    def handle_filter_changed(self, event: Input.Changed) -> None:
        """Re-filter the list immediately as the user types.

        Args:
            event: Textual ``Input.Changed`` message containing the updated
                filter text in ``event.value``.
        """
        self._apply_filter(event.value)

    @on(Input.Submitted, "#filter-input")
    def handle_filter_submitted(self) -> None:
        """Move focus into ``#record-list`` when Enter is pressed in the filter."""
        self.query_one("#record-list", OptionList).focus()

    @on(OptionList.OptionHighlighted, "#record-list")
    def handle_record_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Update ``current_index`` when the user selects another list item.

        Args:
            event: Textual ``OptionList.OptionHighlighted`` message whose
                ``option_index`` gives the highlighted row in the filtered list.
        """
        if 0 <= event.option_index < len(self._filtered_indices):
            target_idx = self._filtered_indices[event.option_index]
            if target_idx != self.current_index:
                self.current_index = target_idx

    def action_focus_filter(self) -> None:
        """Focus the top filter input (bound to ``Ctrl+F``)."""
        self.query_one("#filter-input", Input).focus()


if __name__ == "__main__":
    Stage3DetailsApp(DEFAULT_RECORDS).run()
