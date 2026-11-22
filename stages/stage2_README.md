# Stage 2: Adding a Live Filter Field

- **Code:** [`stage2_filter.py`](./stage2_filter.py)
- **Stylesheet:** [`stage2_filter.tcss`](./stage2_filter.tcss)
- **Run:** `python stages/stage2_filter.py` (or `textual run --dev stages/stage2_filter.py`)

This stage builds on Stage 1 by placing a search `Input` bar at the top of the screen that filters the `OptionList` in real time as you type.

---

## What Changed from Stage 1

- Added `#filter-bar` with `#filter-input` above `#workspace`.
- Added `self._filtered_indices` to track which records match the active query.
- Added `@on(Input.Changed)` and `@on(Input.Submitted)` message handlers.
- Added a `Ctrl+F` binding (`action_focus_filter`) to jump to the filter box from anywhere.

---

## Concepts Introduced

### 1. Stacking Fixed-Height and Flexible Containers in TCSS
In `stage2_filter.tcss`, the screen stacks two content regions between `Header` and `Footer`:

```css
#filter-bar {
    height: auto;        /* Only as tall as the Input box */
    padding: 1 2 0 2;
}

#workspace {
    height: 1fr;         /* Claims all remaining vertical height */
    padding: 1 2;
}
```

Combining `height: auto` for toolbars/headers with `height: 1fr` for the main content pane is one of the most common TCSS layout patterns.

### 2. Index Indirection (`self._filtered_indices`)
Rather than deleting items from `self._records` when filtering, Stage 2 maintains a parallel index list:

```python
self._filtered_indices = [
    i
    for i, rec in enumerate(self._records)
    if not needle or any(needle in str(v).lower() for v in rec.values())
]
```

Why this matters:
- Your source data (`self._records`) stays intact and unmodified.
- Matching across `rec.values()` lets users search by **any** field (`"grace"`, `"8080"`, `"example.com"`, etc.).
- In Stages 3 and 4, `self._filtered_indices[option_index]` maps any visible row in `OptionList` directly back to its true index in `self._records`.

### 3. Event Handling with `@on(MessageClass, "selector")`
Textual widgets emit **Messages** that bubble up the DOM. The `@on` decorator binds a method to a specific message type and CSS selector:

```python
@on(Input.Changed, "#filter-input")
def handle_filter_changed(self, event: Input.Changed) -> None:
    self._apply_filter(event.value)

@on(Input.Submitted, "#filter-input")
def handle_filter_submitted(self) -> None:
    self.query_one("#record-list", OptionList).focus()
```

- **`Input.Changed`** fires on every keystroke, enabling instant live filtering.
- **`Input.Submitted`** fires when the user presses `Enter`; moving focus to `#record-list` lets them switch seamlessly from typing to arrowing through results.

### 4. Dynamically Updating `OptionList`
`_apply_filter()` refreshes the list widget in place without rebuilding the screen:
- `option_list.clear_options()` clears previous matches.
- `option_list.add_options(...)` inserts the matching labels.
- `option_list.border_title` switches between `Items (3)` and `Items (1/3)` to give immediate visual feedback on how many items are filtered.

### 5. Custom Keyboard Actions (`action_*`)
Adding `Binding("ctrl+f", "focus_filter", "Filter")` automatically wires `Ctrl+F` to `action_focus_filter(self)`, which calls `self.query_one("#filter-input", Input).focus()`.

---

**Navigation:** [← Stage 1: Item List](./stage1_README.md) | [Stages Index](./README.md) | [Next: Stage 3 — Item Details →](./stage3_README.md)
