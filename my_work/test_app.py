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

FormValue = str | int | float | bool

# Some data to play with
DEFAULT_SETTINGS: dict[str, FormValue] = {
    "username": "ada_lovelace",
    "email": "ada@example.com",
    "port": 8080,
    "timeout_sec": 3.5,
    "auto_save": True,
    "notifications": False,
}

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
