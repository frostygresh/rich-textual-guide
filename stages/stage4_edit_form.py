"""Stage 4: Full Master-Detail Form with Live Editing, Validation & Reset.

Builds on Stage 3 by turning the right-hand detail pane into a full interactive
edit form for whichever dictionary is selected on the left, while keeping a
live Rich ``Panel`` + ``Pretty`` preview of the selected dict beneath the list.

New concepts introduced in Stage 4:
- Dynamically generating ``Switch`` and typed ``Input`` widgets per Python type
- Async DOM updates (``remove_children()`` + ``mount()``) inside
  ``watch_current_index()`` so switching items rebuilds the form cleanly
- Prev/Next navigation buttons and ``PageUp`` / ``PageDown`` bindings synced
  to the filtered list
- Built-in numeric input validation (``Input.validate()`` + ``Input.-invalid``)
- Typed ``action_save()`` and per-record ``action_reset()`` with toasts
- Retrieving the final edited list via ``app.records`` after ``app.run()``

Run with:
    python stages/stage4_edit_form.py
"""

from __future__ import annotations

from typing import ClassVar

from rich.panel import Panel
from rich.pretty import Pretty
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    Static,
    Switch,
)

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


class Stage4EditFormApp(App[None]):
    """Stage 4 master-detail form that filters, displays, and edits dicts.

    Subclasses ``textual.app.App[None]``, where the generic type argument
    (``None``) specifies the return type of ``App.run()`` (pass a concrete type
    like ``App[list[FormRecord]]`` if you exit via ``self.exit(value)``).

    Args:
        initial_records: Non-empty list of flat dictionaries mapping field
            names (``str``) to scalar values (``str | int | float | bool``).
            Each dictionary is copied internally so the caller's original
            data is never mutated in place.

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

    TITLE = "Stage 4: Editable Form"
    SUB_TITLE = "Filter, inspect & edit a list[dict]"
    CSS_PATH = "stage4_edit_form.tcss"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+f", "focus_filter", "Filter"),
        Binding("pageup", "prev_record", "Prev"),
        Binding("pagedown", "next_record", "Next"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("q", "quit", "Quit"),
    ]

    current_index: reactive[int | None] = reactive(0, init=False)

    def __init__(self, initial_records: list[FormRecord]) -> None:
        """Initialize the app with copies of the provided dictionary records.

        Args:
            initial_records: Non-empty list of flat dictionaries to display and
                edit. Copied internally so caller data is not mutated.

        Raises:
            ValueError: If ``initial_records`` is empty.
        """
        if not initial_records:
            raise ValueError("initial_records must contain at least one dictionary.")
        super().__init__()
        self._defaults: list[FormRecord] = [dict(rec) for rec in initial_records]
        self._records: list[FormRecord] = [dict(rec) for rec in initial_records]
        self._filtered_indices: list[int] = list(range(len(self._records)))

    @property
    def records(self) -> list[FormRecord]:
        """Return shallow copies of all saved dictionaries.

        Returns:
            List of dictionaries reflecting the latest saved edits.
        """
        return [dict(rec) for rec in self._records]

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

    # NEW in Stage 4: map each dictionary field to an editable control widget.
    def _build_field_rows(self, record: FormRecord) -> list[Horizontal]:
        """Create one labeled form row widget for each key/value in ``record``.

        Args:
            record: Dictionary whose entries are mapped to ``Switch`` (for
                ``bool``) or typed ``Input`` (for ``int``, ``float``, ``str``)
                controls.

        Returns:
            List of ``Horizontal`` row containers ready to yield or mount.
        """
        rows: list[Horizontal] = []
        for key, value in record.items():
            label_text = key.replace("_", " ").title()
            widget_id = f"field-{key}"

            # Check `bool` BEFORE `int`, because `bool` subclasses `int`.
            control: Switch | Input
            if isinstance(value, bool):
                control = Switch(value=value, id=widget_id)
            elif isinstance(value, int):
                control = Input(
                    value=str(value),
                    type="integer",
                    id=widget_id,
                    classes="field-input",
                )
            elif isinstance(value, float):
                control = Input(
                    value=str(value),
                    type="number",
                    id=widget_id,
                    classes="field-input",
                )
            else:
                control = Input(
                    value=str(value),
                    type="text",
                    id=widget_id,
                    classes="field-input",
                )

            rows.append(
                Horizontal(
                    Label(f"{label_text}:", classes="field-label"),
                    control,
                    classes="form-row",
                )
            )
        return rows

    def compose(self) -> ComposeResult:
        """Build the top filter bar and master-detail edit workspace.

        Yields:
            Top-level widgets (``Header``, filter bar, master/detail panes, and
            ``Footer``) that form the initial DOM tree.
        """
        yield Header()

        with Horizontal(id="filter-bar"):
            yield Input(
                placeholder="Filter items by any value (Ctrl+F)...",
                id="filter-input",
            )

        with Horizontal(id="workspace"):
            # Left pane (master): item list + live Rich preview of selected dict
            with Vertical(id="list-pane"):
                labels = [
                    self._record_label(i, rec) for i, rec in enumerate(self._records)
                ]
                option_list = OptionList(*labels, id="record-list")
                option_list.border_title = f"Items ({len(self._records)})"
                yield option_list
                with VerticalScroll(id="preview-scroll"):
                    yield Static(id="dict-preview")

            # Right pane (detail): Prev/Next nav + editable form + Save/Reset
            with Vertical(id="detail-pane"):
                with Horizontal(id="record-nav"):
                    yield Button("← Prev", id="prev-btn")
                    yield Label("", id="record-status")
                    yield Button("Next →", id="next-btn")

                with VerticalScroll(id="fields"):
                    yield from self._build_field_rows(self._records[0])

                with Horizontal(id="actions"):
                    yield Button("Save", variant="primary", id="save-btn")
                    yield Button("Reset", variant="warning", id="reset-btn")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize list selection, navigation controls, and Rich preview."""
        option_list = self.query_one("#record-list", OptionList)
        option_list.highlighted = 0
        option_list.focus()
        self._update_nav_controls()
        self._render_preview()

    async def watch_current_index(self, index: int | None) -> None:
        """Rebuild the detail form whenever ``self.current_index`` changes.

        Args:
            index: New index into ``self._records``, or ``None`` when the
                active filter matches zero items.
        """
        fields = self.query_one("#fields", VerticalScroll)
        await fields.remove_children()

        if index is None:
            await fields.mount(
                Label("No items match the current filter.", id="empty-state")
            )
        else:
            await fields.mount(*self._build_field_rows(self._records[index]))

            if index in self._filtered_indices:
                pos = self._filtered_indices.index(index)
                option_list = self.query_one("#record-list", OptionList)
                if option_list.highlighted != pos:
                    option_list.highlighted = pos

        self._update_nav_controls()
        self._render_preview()

    def _apply_filter(self, query: str) -> None:
        """Filter ``#record-list`` to records whose values contain ``query``.

        Args:
            query: Case-insensitive search string typed into ``#filter-input``.
                An empty or whitespace-only string restores all records.
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
            self._update_nav_controls()
            self._render_preview()
        else:
            self.current_index = self._filtered_indices[0]
            option_list.highlighted = 0

    def _update_nav_controls(self) -> None:
        """Update status text and enable/disable Prev, Next, Save, and Reset."""
        status = self.query_one("#record-status", Label)
        prev_btn = self.query_one("#prev-btn", Button)
        next_btn = self.query_one("#next-btn", Button)
        save_btn = self.query_one("#save-btn", Button)
        reset_btn = self.query_one("#reset-btn", Button)

        if (
            self.current_index is None
            or self.current_index not in self._filtered_indices
        ):
            status.update("0 matches")
            prev_btn.disabled = True
            next_btn.disabled = True
            save_btn.disabled = True
            reset_btn.disabled = True
            return

        pos = self._filtered_indices.index(self.current_index)
        visible_count = len(self._filtered_indices)
        status.update(f"Record {pos + 1} of {visible_count}")
        prev_btn.disabled = pos == 0
        next_btn.disabled = pos >= visible_count - 1
        save_btn.disabled = False
        reset_btn.disabled = False

    def _render_preview(self) -> None:
        """Display the currently selected dictionary in a Rich Panel."""
        preview = self.query_one("#dict-preview", Static)
        if self.current_index is None:
            preview.update(
                Panel(
                    "[dim]No matching record.[/]",
                    title="Selected",
                    border_style="yellow",
                )
            )
            return

        idx = self.current_index
        preview.update(
            Panel(
                Pretty(self._records[idx]),
                title=f"Selected (#{idx + 1})",
                border_style="cyan",
            )
        )

    @on(Input.Changed, "#filter-input")
    def handle_filter_changed(self, event: Input.Changed) -> None:
        """Filter the list immediately as the user types.

        Args:
            event: Textual ``Input.Changed`` message containing the updated
                filter string in ``event.value``.
        """
        self._apply_filter(event.value)

    @on(Input.Submitted, "#filter-input")
    def handle_filter_submitted(self) -> None:
        """Move focus from the filter bar into the filtered list on Enter."""
        self.query_one("#record-list", OptionList).focus()

    @on(OptionList.OptionHighlighted, "#record-list")
    def handle_record_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Switch the form when the user clicks or arrows to another record.

        Args:
            event: Textual ``OptionList.OptionHighlighted`` message whose
                ``option_index`` identifies the highlighted row in the
                filtered list.
        """
        if 0 <= event.option_index < len(self._filtered_indices):
            target_idx = self._filtered_indices[event.option_index]
            if target_idx != self.current_index:
                self.current_index = target_idx

    @on(Button.Pressed, "#prev-btn")
    def handle_prev_button(self) -> None:
        """Navigate to the previous visible record when Prev is clicked."""
        self.action_prev_record()

    @on(Button.Pressed, "#next-btn")
    def handle_next_button(self) -> None:
        """Navigate to the next visible record when Next is clicked."""
        self.action_next_record()

    @on(Button.Pressed, "#save-btn")
    @on(Input.Submitted, ".field-input")
    def handle_save(self) -> None:
        """Trigger save when clicking Save or pressing Enter in a form field."""
        self.action_save()

    @on(Button.Pressed, "#reset-btn")
    def handle_reset(self) -> None:
        """Trigger reset for the currently displayed record."""
        self.action_reset()

    def action_focus_filter(self) -> None:
        """Focus the top filter input (bound to ``Ctrl+F``)."""
        self.query_one("#filter-input", Input).focus()

    def action_prev_record(self) -> None:
        """Move to the previous visible dictionary in the filtered list."""
        if self.current_index in self._filtered_indices:
            pos = self._filtered_indices.index(self.current_index)
            if pos > 0:
                self.current_index = self._filtered_indices[pos - 1]

    def action_next_record(self) -> None:
        """Move to the next visible dictionary in the filtered list."""
        if self.current_index in self._filtered_indices:
            pos = self._filtered_indices.index(self.current_index)
            if pos < len(self._filtered_indices) - 1:
                self.current_index = self._filtered_indices[pos + 1]

    def action_save(self) -> None:
        """Validate all widgets and save typed values into the current record."""
        if self.current_index is None:
            return

        idx = self.current_index
        defaults = self._defaults[idx]
        updated: FormRecord = {}
        invalid_fields: list[str] = []
        first_invalid: Input | None = None

        for key, original_value in defaults.items():
            widget_id = f"#field-{key}"

            if isinstance(original_value, bool):
                updated[key] = self.query_one(widget_id, Switch).value
                continue

            inp = self.query_one(widget_id, Input)
            raw = inp.value.strip()

            validation = inp.validate(raw)
            if validation is not None and not validation.is_valid:
                invalid_fields.append(key)
                first_invalid = first_invalid or inp
                continue

            if isinstance(original_value, int):
                updated[key] = int(raw)
            elif isinstance(original_value, float):
                updated[key] = float(raw)
            else:
                updated[key] = raw

        if invalid_fields:
            if first_invalid is not None:
                first_invalid.focus()
            fields_str = ", ".join(invalid_fields)
            self.notify(
                f"Fix invalid value(s): {fields_str}",
                title="Validation Error",
                severity="error",
            )
            return

        self._records[idx] = updated
        if idx in self._filtered_indices:
            pos = self._filtered_indices.index(idx)
            option_list = self.query_one("#record-list", OptionList)
            option_list.replace_option_prompt_at_index(
                pos, self._record_label(idx, updated)
            )
        self._render_preview()
        self.notify(f"Record {idx + 1} updated!", title="Saved")

    def action_reset(self) -> None:
        """Restore the current record and its form widgets to default values."""
        if self.current_index is None:
            return

        idx = self.current_index
        default_record = dict(self._defaults[idx])
        self._records[idx] = default_record

        for key, default_value in default_record.items():
            widget_id = f"#field-{key}"
            if isinstance(default_value, bool):
                self.query_one(widget_id, Switch).value = default_value
            else:
                self.query_one(widget_id, Input).value = str(default_value)

        if idx in self._filtered_indices:
            pos = self._filtered_indices.index(idx)
            option_list = self.query_one("#record-list", OptionList)
            option_list.replace_option_prompt_at_index(
                pos, self._record_label(idx, default_record)
            )
        self._render_preview()
        self.notify(
            f"Restored Record {idx + 1} defaults.", title="Reset", severity="warning"
        )


if __name__ == "__main__":
    app = Stage4EditFormApp(DEFAULT_RECORDS)
    app.run()
    print("Final records:", app.records)
