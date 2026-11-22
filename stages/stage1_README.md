# Stage 1: Displaying a List of Dictionaries

- **Code:** [`stage1_list.py`](./stage1_list.py)
- **Stylesheet:** [`stage1_list.tcss`](./stage1_list.tcss)
- **Run:** `python stages/stage1_list.py` (or `textual run --dev stages/stage1_list.py`)

This stage establishes the foundation of a Textual application: taking a predefined Python `list[dict]` and rendering it as a keyboard- and mouse-navigable list on screen.

---

## Concepts Introduced

### 1. Subclassing `App[None]`
Every Textual application subclasses `textual.app.App`. Writing `App[None]` declares the return type of `app.run()` (here `None`, since the app doesn't pass a return value to `self.exit(...)`).

```python
class Stage1ListApp(App[None]):
    TITLE = "Stage 1: Item List"
    SUB_TITLE = "Displaying a list[dict] with OptionList"
```

`TITLE` and `SUB_TITLE` are picked up automatically by the `Header` widget.

### 2. External Stylesheets (`CSS_PATH`)
Instead of embedding CSS inside Python strings, `CSS_PATH = "stage1_list.tcss"` tells Textual to load styles from a sibling `.tcss` file.

- Textual resolves relative paths against the Python file's directory, so `python stages/stage1_list.py` works from any working directory.
- Under `textual run --dev stages/stage1_list.py`, saving changes to `stage1_list.tcss` hot-reloads the UI immediately.

### 3. Keyboard Shortcuts (`BINDINGS`)
`BINDINGS` maps keys to `action_<name>` methods and automatically populates both the `Footer` bar and the built-in Command Palette (`Ctrl+P`):

```python
BINDINGS: ClassVar[list[BindingType]] = [
    Binding("q", "quit", "Quit"),
]
```

- `"quit"` uses Textual's built-in `App.action_quit()`.
- Annotating with `ClassVar[list[BindingType]]` matches `App.BINDINGS` and avoids Ruff's `RUF012` mutable-class-default warning.

### 4. Composing the Widget Tree (`compose()`)
`compose()` is a generator that yields the initial DOM tree. Context managers like `with Vertical(id="workspace"):` nest child widgets inside containers:

```python
def compose(self) -> ComposeResult:
    yield Header()
    with Vertical(id="workspace"):
        labels = [self._record_label(i, rec) for i, rec in enumerate(self._records)]
        option_list = OptionList(*labels, id="record-list")
        option_list.border_title = f"Items ({len(self._records)})"
        yield option_list
    yield Footer()
```

- **`OptionList`** renders a scrollable, selectable list of items with built-in arrow-key and mouse support.
- **`border_title`** places a label directly inside the widget's top border.

#### `return` vs. `yield` in `compose()`

If you're used to regular Python functions, you might wonder why `compose()` uses `yield` instead of `return` (while `_record_label()` right above it uses `return`):

| | `return` | `yield` |
| :--- | :--- | :--- |
| **How many values** | Sends back **one** value (e.g., a single string in `_record_label()`) | Produces a **sequence** of values one at a time (a generator) |
| **Function lifetime** | **Exits immediately** and discards local state | **Pauses** at the `yield` line, keeps local state alive, and **resumes** on the next step |
| **Inside a `with` block** | Closes the `with` block immediately on exit | Keeps the `with` block **active** across multiple `yield` statements |

Why Textual relies on `yield` in `compose()`:
1. **Multiple widgets without building lists by hand:** `compose()` streams `Header()`, then the workspace widgets, then `Footer()` cleanly in top-to-bottom order.
2. **Context-manager nesting (`with Vertical(...):`):** Because `yield` pauses *inside* the `with` block instead of exiting the function, Textual knows that every widget yielded while inside `with Vertical(id="workspace"):` belongs as a **child** of `#workspace`. When execution leaves the `with` block, Textual automatically closes that container before yielding `Footer()`. With `return`, the function would terminate on the very first widget and couldn't express nested parent/child layouts this way.
3. **Shortcut for many widgets (`yield from`):** In later stages, you'll also see `yield from self._build_field_rows(...)`, which yields every widget in a list one by one inside the active container.

### 5. Lifecycle: `__init__()` vs. `on_mount()`
- **`__init__()`** stores application data (`self._records = [dict(rec) for rec in initial_records]`, copied so the caller's list isn't mutated). Never query widgets here—the DOM does not exist yet.
- **`on_mount()`** runs once all widgets from `compose()` are mounted. That's where we look up `#record-list` via `self.query_one("#record-list", OptionList)`, highlight item `0`, and focus it so arrow keys work immediately.

### 6. Core TCSS Layout Primitives (`stage1_list.tcss`)
- `Screen { layout: vertical; }` stacks `Header`, `#workspace`, and `Footer` top-to-bottom.
- `height: 1fr` (fractional unit) stretches `#workspace` and `#record-list` to fill all available vertical space.
- `padding: 1 2` adds 1 terminal row top/bottom and 2 columns left/right.
- `border: round $accent` draws a rounded Unicode border using the active theme's `$accent` color.

---

**Navigation:** [Stages Index](./README.md) | [Next: Stage 2 — Live Filter →](./stage2_README.md)
