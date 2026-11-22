# Building the Dictionary Master–Detail Form in 4 Stages

This folder breaks the dictionary form app into four standalone, runnable stages so you can study one Rich/Textual concept at a time. Each stage builds directly on the previous one and keeps its layout in a matching `.tcss` file.

| Stage | Guide | Files | What's Added | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | [Stage 1 Guide](./stage1_README.md) | [`stage1_list.py`](./stage1_list.py) + [`stage1_list.tcss`](./stage1_list.tcss) | Display a predefined `list[dict]` in a Textual `OptionList` with `Header`, `Footer`, `BINDINGS`, and external `CSS_PATH`. | `python stages/stage1_list.py` |
| **Stage 2** | [Stage 2 Guide](./stage2_README.md) | [`stage2_filter.py`](./stage2_filter.py) + [`stage2_filter.tcss`](./stage2_filter.tcss) | Add a top `#filter-input` bar with `@on(Input.Changed)`, `Ctrl+F` focus shortcut, and `_filtered_indices` mapping. | `python stages/stage2_filter.py` |
| **Stage 3** | [Stage 3 Guide](./stage3_README.md) | [`stage3_details.py`](./stage3_details.py) + [`stage3_details.tcss`](./stage3_details.tcss) | Split into a master–detail view: left item list + right read-only details rendered with Rich `Table.grid`, `Panel`, and `Pretty`, driven by a `reactive` index. | `python stages/stage3_details.py` |
| **Stage 4** | [Stage 4 Guide](./stage4_README.md) | [`stage4_edit_form.py`](./stage4_edit_form.py) + [`stage4_edit_form.tcss`](./stage4_edit_form.tcss) | Turn the right pane into an interactive edit form (`Input`/`Switch` per Python type), add validation, Prev/Next navigation, typed Save, and per-record Reset. | `python stages/stage4_edit_form.py` |

## Live CSS Reloading

You can run any stage in Textual dev mode (requires `pip install textual-dev`) to hot-reload edits to its `.tcss` file while the app is running:

```bash
textual run --dev stages/stage1_list.py
textual run --dev stages/stage2_filter.py
textual run --dev stages/stage3_details.py
textual run --dev stages/stage4_edit_form.py
```

> [!NOTE]
> **Windows CLI note:** If the `textual` command isn't recognized on Windows (common when Python's `Scripts` directory isn't on `PATH`), run it through Python with `-m`:
> - **Dev CLI (`textual-dev`):** `python -m textual_dev.cli run --dev stages/stage1_list.py` (and `python -m textual_dev.cli console` for the debug console)
> - **Built-in Textual demo showcase:** `python -m textual` (note that `python -m textual` always launches Textual's built-in `DemoApp`, not the `textual run --dev` CLI)
