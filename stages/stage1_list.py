"""Stage 1: Display a List of Dictionaries in Textual.

This first stage focuses strictly on displaying a predefined ``list[dict]``
inside a Textual ``OptionList`` widget, styled by an external TCSS file.

Concepts introduced in Stage 1:
- Subclassing ``textual.app.App[None]`` and loading styles via ``CSS_PATH``
- Defining keyboard shortcuts with ``BINDINGS: ClassVar[list[BindingType]]``
- Building the DOM in ``compose()`` with ``Header``, ``OptionList``, ``Footer``
- Focusing and highlighting the initial list item in ``on_mount()``

Run with:
    python stages/stage1_list.py
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.widgets import Footer, Header, OptionList

# Type aliases for the scalar values and dictionary records in our list.
FormValue = str | int | float | bool
FormRecord = dict[str, FormValue]

# Predefined list (array) of dictionaries to display.
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


class Stage1ListApp(App[None]):
    """Stage 1 app that displays a list of dictionary items in an OptionList.

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

    TITLE = "Stage 1: Item List"
    SUB_TITLE = "Displaying a list[dict] with OptionList"
    CSS_PATH = "stage1_list.tcss"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, initial_records: list[FormRecord]) -> None:
        """Initialize the app with shallow copies of ``initial_records``.

        Args:
            initial_records: Non-empty list of dictionaries to display.

        Raises:
            ValueError: If ``initial_records`` is empty.
        """
        if not initial_records:
            raise ValueError("initial_records must contain at least one dictionary.")
        super().__init__()
        self._records: list[FormRecord] = [dict(rec) for rec in initial_records]

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
        """Build the initial widget tree with a Header, item list, and Footer.

        Yields:
            Top-level widgets (``Header``, list container, and ``Footer``).
        """
        # 1. Dock the top bar; automatically displays `TITLE` and `SUB_TITLE`.
        yield Header()

        # 2. Open a vertical layout container (`#workspace` in stage1_list.tcss).
        #    Because `yield` pauses inside this `with` block, every widget
        #    yielded here is mounted as a child of `#workspace`.
        with Vertical(id="workspace"):
            # 3. Convert each dictionary into a display string ("1. ada_lovelace").
            labels = [
                self._record_label(i, rec) for i, rec in enumerate(self._records)
            ]
            # 4. Unpack the labels into a selectable list and tag it with an ID
            #    so TCSS (`#record-list`) and `on_mount()` can target it.
            option_list = OptionList(*labels, id="record-list")
            # 5. Display the item count directly inside the list's top border.
            option_list.border_title = f"Items ({len(self._records)})"
            # 6. Yield the OptionList into the `#workspace` container.
            yield option_list

        # 7. Dock the bottom keybinding bar, auto-populated from `BINDINGS`.
        yield Footer()

    # Textual calls `on_mount()` automatically once every widget yielded by
    # `compose()` has been mounted into the DOM. It is needed because widgets
    # do not exist yet during `__init__()` (and aren't mounted yet during
    # `compose()`), so DOM lookups and initial keyboard focus must happen here.
    def on_mount(self) -> None:
        """Highlight and focus the first list item once the DOM is mounted."""
        # Look up the mounted OptionList by its `#record-list` ID selector;
        # passing `OptionList` verifies its type at runtime and for editors.
        option_list = self.query_one("#record-list", OptionList)
        # Pre-select the first row (0-based index) on startup.
        option_list.highlighted = 0
        # Give the list keyboard focus so Up/Down arrow keys work immediately
        # without requiring the user to click it or press Tab first.
        option_list.focus()


if __name__ == "__main__":
    Stage1ListApp(DEFAULT_RECORDS).run()
