"""Stage 2: Add a Live Filter Input Above the Item List.

Builds on Stage 1 by adding a search/filter ``Input`` bar at the top of the
screen that narrows the ``OptionList`` live as the user types.

New concepts introduced in Stage 2:
- Adding a top ``#filter-bar`` container with an ``Input`` widget
- Tracking visible record indices in ``self._filtered_indices``
- Handling ``Input.Changed`` for live filtering and ``Input.Submitted`` to move
  focus into the filtered list on Enter
- Adding a ``Ctrl+F`` keyboard binding to jump to the filter field from anywhere

Run with:
    python stages/stage2_filter.py
"""

from __future__ import annotations

from typing import ClassVar

# `@on` is Textual's decorator for routing widget Messages (events) to methods.
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, OptionList

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


class Stage2FilterApp(App[None]):
    """Stage 2 app adding a live top filter field above the item list.

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
    """

    TITLE = "Stage 2: Filterable List"
    SUB_TITLE = "Live filtering with Input.Changed"
    CSS_PATH = "stage2_filter.tcss"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+f", "focus_filter", "Filter"),
        Binding("q", "quit", "Quit"),
    ]

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
        # Maps visible OptionList row positions back to real `self._records` indices.
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

    def compose(self) -> ComposeResult:
        """Build the top filter bar above the selectable item list.

        Yields:
            Top-level widgets (``Header``, filter bar, workspace, ``Footer``).
        """
        yield Header()

        # NEW in Stage 2: top filter bar spanning the screen width.
        with Horizontal(id="filter-bar"):
            yield Input(
                placeholder="Filter items by any value (Ctrl+F)...",
                id="filter-input",
            )

        with Vertical(id="workspace"):
            labels = [
                self._record_label(i, rec) for i, rec in enumerate(self._records)
            ]
            option_list = OptionList(*labels, id="record-list")
            option_list.border_title = f"Items ({len(self._records)})"
            yield option_list

        yield Footer()

    def on_mount(self) -> None:
        """Highlight the first item and focus the filter bar on startup."""
        option_list = self.query_one("#record-list", OptionList)
        option_list.highlighted = 0
        self.query_one("#filter-input", Input).focus()

    def _apply_filter(self, query: str) -> None:
        """Filter ``#record-list`` to records whose values contain ``query``.

        Args:
            query: Case-insensitive search text from ``#filter-input``. An
                empty or whitespace-only string shows all records.
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
        if self._filtered_indices:
            option_list.highlighted = 0

    # -------------------------------------------------------------------------
    # Event Handlers (`@on` decorator)
    # -------------------------------------------------------------------------
    # Textual widgets communicate by posting Message objects (events) that
    # bubble up the DOM tree to the App. `@on(MessageClass, "css-selector")`
    # binds a method to a specific message from matching widgets—cleaner than
    # the `on_input_changed` naming convention because you can pick any method
    # name and scope it to `#filter-input` so future Inputs won't trigger it.
    #
    # `Input.Changed` fires on every keystroke, passing the new text in
    # `event.value`.
    @on(Input.Changed, "#filter-input")
    def handle_filter_changed(self, event: Input.Changed) -> None:
        """Re-filter the list immediately on every keystroke.

        Args:
            event: Textual ``Input.Changed`` message containing the updated
                text in ``event.value``.
        """
        self._apply_filter(event.value)

    # `Input.Submitted` fires when the user presses Enter inside `#filter-input`.
    # Notice that the `event` parameter is optional with `@on`: when a handler
    # doesn't need data from the message, you can omit `event` completely.
    @on(Input.Submitted, "#filter-input")
    def handle_filter_submitted(self) -> None:
        """Move focus into ``#record-list`` when Enter is pressed in the filter."""
        self.query_one("#record-list", OptionList).focus()

    def action_focus_filter(self) -> None:
        """Focus the top filter input (bound to ``Ctrl+F``)."""
        self.query_one("#filter-input", Input).focus()


if __name__ == "__main__":
    Stage2FilterApp(DEFAULT_RECORDS).run()
