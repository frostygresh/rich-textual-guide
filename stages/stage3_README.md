# Stage 3: Displaying Details for the Selected Item

- **Code:** [`stage3_details.py`](./stage3_details.py)
- **Stylesheet:** [`stage3_details.tcss`](./stage3_details.tcss)
- **Run:** `python stages/stage3_details.py` (or `textual run --dev stages/stage3_details.py`)

This stage turns the single-column list into a **master–detail** interface: selecting any item in the left list immediately renders its formatted fields and raw dictionary on the right using Rich renderables.

---

## What Changed from Stage 2

- Changed `#workspace` from `Vertical` to `Horizontal`, splitting it into `#list-pane` (left) and `#detail-pane` (right).
- Added a reactive `current_index: reactive[int | None]` attribute with a `watch_current_index()` watcher.
- Added an `@on(OptionList.OptionHighlighted, "#record-list")` handler.
- Added Rich rendering (`Table.grid`, `Panel`, `Pretty`, and Rich markup) inside Textual `Static` widgets.

---

## Concepts Introduced

### 1. Master–Detail Layout with Fractional Units (`1fr` vs. `2fr`)
In `stage3_details.tcss`, placing two containers inside a `Horizontal` `#workspace` creates a responsive side-by-side split:

```css
#list-pane {
    width: 1fr;         /* 1/3 of the available width */
    min-width: 26;      /* Prevents the list from shrinking too narrow */
    margin-right: 2;
}

#detail-pane {
    width: 2fr;         /* 2/3 of the available width */
    border: round $primary;
    padding: 1 2;
}
```

Wrapping the right pane in `VerticalScroll` ensures long dictionaries remain scrollable on smaller terminals.

### 2. Reactive State (`reactive`) and Watchers (`watch_*`)
Instead of manually calling `_render_details()` from every code path that might change selection, Stage 3 declares a reactive attribute:

```python
current_index: reactive[int | None] = reactive(0, init=False)

def watch_current_index(self, index: int | None) -> None:
    self._render_details()
```

- Whenever `self.current_index` changes (via arrow keys, mouse click, or filtering), Textual automatically runs `watch_current_index()`.
- Setting `init=False` prevents the watcher from firing during `__init__()` before the DOM is mounted.
- Using `int | None` models both a valid selection (`0`, `1`, `2`) and the empty-filter state (`None`).

### 3. Translating Filtered Selection (`OptionList.OptionHighlighted`)
When the user clicks or arrows to an item in `#record-list`, `event.option_index` is the row's position within the **filtered** list. We map it through `self._filtered_indices` to get the real index in `self._records`:

```python
@on(OptionList.OptionHighlighted, "#record-list")
def handle_record_highlighted(self, event: OptionList.OptionHighlighted) -> None:
    if 0 <= event.option_index < len(self._filtered_indices):
        target_idx = self._filtered_indices[event.option_index]
        if target_idx != self.current_index:
            self.current_index = target_idx
```

### 4. Embedding Rich Renderables Inside Textual
Textual's `Static.update(...)` accepts any Rich renderable. Stage 3 showcases three Rich tools working together:

- **`Table.grid(expand=True, padding=(0, 2))`** — creates a borderless multi-column grid aligning `Field`, `Value`, and Python `Type`.
- **Rich Console Markup** — `_format_value()` styles values by type (`[bold green]True[/]`, `[bold red]False[/]`, `[cyan]8080[/]`).
- **`Panel` & `Pretty`** — wraps both the grid and `Pretty(record)` in titled, theme-colored boxes.

### 5. Handling Zero Filter Matches Gracefully
If a filter query matches nothing, `_apply_filter()` sets `self.current_index = None`, and `_render_details()` displays a yellow empty-state `Panel` instead of crashing on an out-of-range index.

---

**Navigation:** [← Stage 2: Live Filter](./stage2_README.md) | [Stages Index](./README.md) | [Next: Stage 4 — Editable Form →](./stage4_README.md)
