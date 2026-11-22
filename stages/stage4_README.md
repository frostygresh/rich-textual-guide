# Stage 4: Editing Item Data with a Dynamic Form

- **Code:** [`stage4_edit_form.py`](./stage4_edit_form.py)
- **Stylesheet:** [`stage4_edit_form.tcss`](./stage4_edit_form.tcss)
- **Run:** `python stages/stage4_edit_form.py` (or `textual run --dev stages/stage4_edit_form.py`)

This final stage transforms the read-only detail pane from Stage 3 into a full interactive form where users can edit, validate, save, and reset any dictionary in the list while viewing a live Rich preview of the selected record.

---

## What Changed from Stage 3

- Replaced the read-only Rich detail card with dynamically generated form controls (`Input` and `Switch`), Prev/Next navigation (`PageUp` / `PageDown`), and Save/Reset buttons (`Ctrl+S` / `Ctrl+R`).
- Moved the live Rich `Panel(Pretty(...))` preview beneath `#record-list` in the left pane.
- Kept separate copies of `self._defaults` and `self._records` so Reset restores original values per record.
- Exposed `app.records` so callers can read the final edited list after `app.run()` exits.

---

## Concepts Introduced

### 1. Dynamic Form Generation by Python Type (`_build_field_rows`)
Each dictionary entry is mapped to the right Textual widget based on its runtime Python type, with a deterministic CSS ID (`id=f"field-{key}"`):

| Python Type | Textual Widget | Built-In Behavior |
| :--- | :--- | :--- |
| `bool` | `Switch(value=value)` | On/off toggle (checked **before** `int`, because `bool` subclasses `int`!) |
| `int` | `Input(type="integer")` | Restricts input to valid integers and validates on save |
| `float` | `Input(type="number")` | Restricts input to valid decimals and validates on save |
| `str` | `Input(type="text")` | Free-form text input |

### 2. Async DOM Updates (`remove_children()` + `mount()`)
Because different records can even have different keys or types, `watch_current_index()` is an `async def` watcher that swaps out the form rows dynamically:

```python
async def watch_current_index(self, index: int | None) -> None:
    fields = self.query_one("#fields", VerticalScroll)
    await fields.remove_children()

    if index is None:
        await fields.mount(Label("No items match the current filter.", id="empty-state"))
    else:
        await fields.mount(*self._build_field_rows(self._records[index]))
```

### 3. Scoping `@on` Selectors for Multiple `Input` Widgets
Now that the app has **both** `#filter-input` and form field inputs (`.field-input`), scoping the `@on` selector keeps `Enter` doing the right thing in each place:

- `@on(Input.Submitted, "#filter-input")` → moves focus into `#record-list`.
- `@on(Input.Submitted, ".field-input")` + `@on(Button.Pressed, "#save-btn")` → runs `action_save()`.

### 4. Input Validation, `Input.-invalid`, and Typed Conversion
In `action_save()`:
1. Each `Input` is checked via `inp.validate(raw)`. Textual also automatically toggles the `-invalid` CSS class on failing inputs, which `stage4_edit_form.tcss` styles with `Input.-invalid { border: tall $error; }`.
2. If any field is invalid, focus jumps to the first invalid input, a red error toast appears (`self.notify(..., severity="error")`), and `self._records` is not overwritten.
3. Valid values are converted back to the original Python type (`bool`, `int`, `float`, or `str`), saved into `self._records[idx]`, and reflected immediately in `#record-list` (via `replace_option_prompt_at_index`) and the Rich `Pretty` preview.

### 5. Per-Record Reset & Filtered Navigation
- **`action_prev_record()` / `action_next_record()`** step through `self._filtered_indices`, keeping `← Prev`, `Next →`, and `Record X of Y` accurate even while a filter is active.
- **`action_reset()`** restores only `self._records[idx]` from `self._defaults[idx]` and writes those values back into every form widget.
- **Retrieving results**: After exiting the TUI (`q`), `app.records` returns copies of all saved dictionaries.

---

**Navigation:** [← Stage 3: Item Details](./stage3_README.md) | [Stages Index](./README.md)
