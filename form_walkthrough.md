# Walkthrough: Building a Textual Form from a Predefined Dictionary

This walkthrough shows how to turn a plain Python `dict` into an interactive Textual form that:
- Displays each key/value pair using the right Textual widget (`Input` or `Switch`),
- Validates numeric fields automatically,
- Converts edited values back into their original Python types on **Save**,
- Restores defaults on **Reset**, and
- Renders a live preview of the dictionary using Rich's `Panel` + `Pretty`.

The complete runnable script is in [`dict_form.py`](./dict_form.py) with its external stylesheet in [`dict_form.tcss`](./dict_form.tcss).

---

## Step 1: Import the Needed Modules

Create a new file (for example, `dict_form.py`) and import the standard library, **Rich**, and **Textual** components you'll use across the form:

```python
from __future__ import annotations

from typing import ClassVar

# Rich renderables for the live dictionary preview pane
from rich.panel import Panel
from rich.pretty import Pretty

# Textual core app, event decorator, bindings, layout containers, and widgets
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, Static, Switch
```

What each group of imports provides:
- **`__future__.annotations` & `ClassVar`**: Enables modern type syntax and lets us annotate class-level `BINDINGS` cleanly for linters and type checkers.
- **`rich.panel.Panel` & `rich.pretty.Pretty`**: Renders the dictionary with syntax highlighting inside a titled box.
- **`textual.on`**: Decorator that connects widget events (like `Button.Pressed` or `Input.Submitted`) to handler methods using CSS selectors.
- **`App`, `ComposeResult`, `Binding`, `BindingType`**: Base application class, return type for `compose()`, and keyboard shortcut definitions.
- **`Horizontal`, `Vertical`, `VerticalScroll`**: Layout containers to arrange form rows, panes, and scrollable fields.
- **`Header`, `Footer`, `Label`, `Input`, `Switch`, `Button`, `Static`**: The built-in UI widgets that make up the form and preview card.

---

## Step 2: Define the Predefined Dictionary

Start with a flat dictionary of settings or record data. Each key will become a form label, and each value's Python type (`str`, `int`, `float`, `bool`) tells Textual which widget to render:

```python
FormValue = str | int | float | bool

DEFAULT_SETTINGS: dict[str, FormValue] = {
    "username": "ada_lovelace",
    "email": "ada@example.com",
    "port": 8080,
    "timeout_sec": 3.5,
    "auto_save": True,
    "notifications": False,
}
```

> [!TIP]
> Always store a **copy** of the dictionary inside your `App.__init__()` (`self._defaults = dict(initial_data)` and `self._data = dict(initial_data)`) so you don't mutate the caller's dictionary in place and your **Reset** button always has clean defaults to restore.

---

## Step 3: Map Dictionary Entries to Widgets in `compose()`

In Textual, `compose()` builds the widget tree by yielding widgets. Because it is normal Python, you can loop directly over `self._data.items()` to generate one row per dictionary key:

```python
with VerticalScroll(id="fields"):
    for key, value in self._data.items():
        label_text = key.replace("_", " ").title()
        widget_id = f"field-{key}"

        with Horizontal(classes="form-row"):
            yield Label(f"{label_text}:", classes="field-label")

            # Check bool BEFORE int (in Python, bool is a subclass of int!)
            if isinstance(value, bool):
                yield Switch(value=value, id=widget_id)
            elif isinstance(value, int):
                yield Input(
                    value=str(value),
                    type="integer",
                    id=widget_id,
                    classes="field-input",
                )
            elif isinstance(value, float):
                yield Input(
                    value=str(value), type="number", id=widget_id, classes="field-input"
                )
            else:
                yield Input(
                    value=str(value), type="text", id=widget_id, classes="field-input"
                )
```

Key Textual patterns used here:
- **Deterministic IDs (`id=f"field-{key}"`)** let you look up any key's widget later with `self.query_one(f"#field-{key}", Input)`.
- **`VerticalScroll`** ensures the form remains usable even if the dictionary grows to dozens of keys.
- **Built-in `Input` types**: `type="integer"` and `type="number"` automatically reject non-numeric characters and run validation when reading the field.
- **`isinstance(value, bool)` comes first**: In Python, `isinstance(True, int)` is `True`, so checking `bool` before `int` guarantees booleans become `Switch` toggles instead of integer text boxes.

---

## Step 4: Lay Out the Form with TCSS

Textual uses **TCSS (Textual CSS)**—a CSS-inspired stylesheet language—to control layout, sizing, spacing, borders, and colors separately from your Python logic.

### How TCSS Is Attached to Your App

There are two ways to load TCSS on an `App` (or `Screen` / custom `Widget`):

1. **External file via `CSS_PATH`** (what [`dict_form.py`](./dict_form.py) uses—recommended as apps grow):
   ```python
   class DictFormApp(App[None]):
       CSS_PATH = "dict_form.tcss"
   ```
   Textual resolves `CSS_PATH` relative to the Python file defining the class. Using an external `.tcss` file gives you editor syntax highlighting and **instant live-reloading** when running `textual run --dev dict_form.py`—saving the `.tcss` file updates the running terminal UI without restarting the app.
2. **Inline via `CSS`** (convenient for tiny single-file prototypes):
   ```python
   class DictFormApp(App[None]):
       CSS = """
       ...
       """
   ```

### The Stylesheet (`dict_form.tcss`)

Create [`dict_form.tcss`](./dict_form.tcss) in the same folder as `dict_form.py` and point `DictFormApp` to it with `CSS_PATH = "dict_form.tcss"`:

```css
/* Stylesheet for DictFormApp (dict_form.py)
 * Run `textual run --dev dict_form.py` to hot-reload edits to this file live.
 */

/* Root screen: stack Header, #workspace, and Footer top-to-bottom. */
Screen {
    layout: vertical;
}

/* Main two-pane area between Header and Footer. */
#workspace {
    height: 1fr;        /* Fill all remaining vertical space */
    padding: 1 2;       /* 1 cell top/bottom, 2 cells left/right */
}

/* Left pane holding the generated form fields and action buttons. */
#form-pane {
    width: 2fr;             /* Take 2/3 of the workspace width */
    margin-right: 2;        /* Gap between form pane and preview pane */
    border: round $primary; /* Rounded box border using theme primary */
    padding: 1 2;           /* Inner breathing room inside the border */
}

/* Right pane holding the live Rich dictionary preview. */
#preview-pane {
    width: 1fr;             /* Take the remaining 1/3 of workspace width */
}

/* Scrollable container for form rows so long dicts never clip off-screen. */
#fields {
    height: 1fr;            /* Expand to push #actions to the bottom */
}

/* One horizontal row per dictionary key: Label on left, control on right. */
.form-row {
    height: auto;           /* Wrap tightly around the tallest child */
    align-vertical: middle; /* Center Label vertically with Input/Switch */
    margin-bottom: 1;       /* 1 blank row of spacing between fields */
}

/* Fixed-width left column so all inputs line up cleanly down the form. */
.field-label {
    width: 18;              /* 18 character cells wide */
    padding-right: 1;       /* Small gap between label text and control */
    text-style: bold;       /* Make field names stand out */
}

/* Text/numeric inputs stretch across whatever row width remains. */
.field-input {
    width: 1fr;
}

/* Textual adds the `-invalid` class automatically when Input validation
   fails (e.g. non-integer text in `type="integer"`). */
Input.-invalid {
    border: tall $error;    /* Highlight invalid fields in theme error */
}

/* Footer row inside #form-pane for the Save and Reset buttons. */
#actions {
    height: auto;             /* Only as tall as the buttons need */
    padding-top: 1;           /* Space between divider line and buttons */
    border-top: solid $panel; /* Subtle horizontal divider above buttons */
}

/* Descendant selector: add spacing between buttons inside #actions. */
#actions Button {
    margin-right: 1;
}

/* Let the Rich Panel preview size itself to fit the dictionary lines. */
#dict-preview {
    height: auto;
}
```

### How Each Piece Works

- **Selectors connect CSS rules to widgets from `compose()`**:
  - **`#id` selectors** (`#workspace`, `#form-pane`, `#actions`) target a single widget created with `id="workspace"`, etc.
  - **`.class` selectors** (`.form-row`, `.field-label`, `.field-input`) match widgets created with `classes="form-row"`, etc., styling every dynamically generated row and label consistently.
  - **Type & descendant selectors**: `Screen` targets the root screen, and `#actions Button` adds right spacing only to `Button` widgets nested inside `#actions`.
  - **State classes (`Input.-invalid`)**: Textual automatically toggles `-invalid` / `-valid` on `Input` widgets as the user types, so you get red error borders without writing extra Python code.
- **Sizing units control responsive layout**:
  - **Cells (`18`, `1 2`)**: Measured in terminal character cells. `padding: 1 2` means 1 row top/bottom and 2 columns left/right.
  - **`auto`**: Shrinks a widget or container to fit its content (`height: auto` keeps each `.form-row` and the `#actions` bar compact instead of stretching).
  - **Fractions (`1fr`, `2fr`)**: Distribute leftover space proportionally. Giving `#form-pane` `width: 2fr` and `#preview-pane` `width: 1fr` creates a responsive 2:1 split that adapts when the terminal is resized; `.field-input { width: 1fr; }` stretches every text box across whatever width remains after the 18-cell label.
- **Alignment & Borders**:
  - `align-vertical: middle` centers the `Label` vertically alongside taller controls like `Input` and `Switch`.
  - `border: round $primary` draws rounded Unicode box borders; `border-top: solid $panel` adds a subtle divider line above the Save/Reset buttons.
- **Theme variables (`$primary`, `$panel`, `$error`)**:
  - Instead of hardcoding colors like `#ff0000`, theme variables resolve dynamically from the active Textual theme so the form stays readable in both dark and light themes.
- **Comments**: Always use `/* ... */` inside TCSS (never `#`, which starts an ID selector).

---

## Step 5: Render a Live Rich Preview of the Dictionary

Place a `Static(id="dict-preview")` widget in the right-hand pane and update it with Rich's `Pretty` renderable wrapped in a `Panel`:

```python
def on_mount(self) -> None:
    self._render_preview()


def _render_preview(self) -> None:
    preview = self.query_one("#dict-preview", Static)
    preview.update(
        Panel(
            Pretty(self._data),
            title="Saved Dictionary",
            border_style="cyan",
        )
    )
```

`Pretty` syntax-highlights Python dictionaries, types, booleans, and numbers automatically—so the user immediately sees whether `"port"` is an `int` (`8080`) or `"auto_save"` is a `bool` (`True`).

---

## Step 6: Wire Up Save, Validation, and Reset

Use `@on` decorators to connect buttons (and pressing **Enter** inside any `Input`) to action methods, and pair them with `BINDINGS` (`Ctrl+S`, `Ctrl+R`, `Q`) for keyboard-first navigation:

```python
BINDINGS: ClassVar[list[BindingType]] = [
    Binding("ctrl+s", "save", "Save"),
    Binding("ctrl+r", "reset", "Reset"),
    Binding("q", "quit", "Quit"),
]


@on(Button.Pressed, "#save-btn")
@on(Input.Submitted)
def handle_save(self) -> None:
    self.action_save()


@on(Button.Pressed, "#reset-btn")
def handle_reset(self) -> None:
    self.action_reset()
```

Inside `action_save()`, iterate over `self._defaults.items()`, read each widget by its `#field-{key}` ID, validate `Input` fields, and convert each string back to its original Python type:

```python
def action_save(self) -> None:
    updated: dict[str, FormValue] = {}
    invalid_fields: list[str] = []
    first_invalid: Input | None = None

    for key, original_value in self._defaults.items():
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
        self.notify(
            f"Fix invalid value(s): {', '.join(invalid_fields)}",
            title="Validation Error",
            severity="error",
        )
        return

    self._data = updated
    self._render_preview()
    self.notify("Dictionary updated!", title="Saved")
```

And `action_reset()` reverses the flow—writing `self._defaults` back into each widget's `.value`:

```python
def action_reset(self) -> None:
    self._data = dict(self._defaults)

    for key, default_value in self._defaults.items():
        widget_id = f"#field-{key}"
        if isinstance(default_value, bool):
            self.query_one(widget_id, Switch).value = default_value
        else:
            self.query_one(widget_id, Input).value = str(default_value)

    self._render_preview()
    self.notify("Restored original values.", title="Reset", severity="warning")
```

---

## Step 7: Run & Retrieve the Updated Dictionary

Run the script from your terminal:

```bash
python dict_form.py
```

When you exit (`q`), `app.data` contains the final validated, properly typed dictionary:

```python
if __name__ == "__main__":
    app = DictFormApp(DEFAULT_SETTINGS)
    app.run()
    print("Final dictionary:", app.data)
```

### Ideas to Extend This Form
- **Dropdown choices (`Select`)**: Pass a `choices: dict[str, list[str]]` map alongside your dictionary to render a `Select` widget for enumerated fields like `"environment": "prod"`.
- **Custom validators**: Attach `textual.validation.Regex` or `Number(minimum=1, maximum=65535)` to specific keys (for example, validating `"email"` or `"port"` range).
- **Persist to JSON**: In `action_save()`, write `json.dumps(self._data, indent=2)` to a config file on disk.
