# AGENTS.md — textual-emoji-picker

Developer and agent guide for contributing to this package. Read this before
writing or modifying any code.

---

## What this package is

A Textual `Widget` that lets users pick an emoji from the full Unicode 15 set.
It is a standalone library extracted from [telemente](https://github.com/telemente/telemente).
The public API is intentionally minimal: one widget class, two message types.

---

## Repository layout

```
textual-emoji-picker/
├── pyproject.toml                          # build config, tool settings
├── README.md                               # user-facing documentation
├── AGENTS.md                               # this file
├── LICENSE
├── py.typed                                # PEP 561 — sdist marker
├── scripts/
│   └── generate_categories.py             # regenerates _data/categories.json
├── src/
│   └── textual_emoji_picker/
│       ├── __init__.py                     # public API: EmojiPicker only
│       ├── _widget.py                      # EmojiPicker(Widget) — all logic lives here
│       ├── _data/
│       │   └── categories.json            # bundled Unicode category data
│       └── py.typed                        # PEP 561 — wheel marker
└── tests/
    ├── test_data.py                        # Tier-1: data integrity, no Textual
    └── test_widget.py                      # Tier-2: widget behaviour via pilot
```

### What is NOT public

- `_widget.py` — module, not a public import path. Import `EmojiPicker` from
  `textual_emoji_picker` directly, never from `textual_emoji_picker._widget`.
- All functions and variables prefixed with `_` are private implementation
  details subject to change without notice.
- `_data/categories.json` — treated as an opaque data file. Do not parse it
  directly from outside the package; use the widget's constructor kwargs to
  filter categories.

---

## Public API surface

```python
from textual_emoji_picker import EmojiPicker

# Messages
EmojiPicker.EmojiSelected   # .emoji: str — selected codepoint (tone applied)
EmojiPicker.Cancelled       # no payload — Escape was pressed

# Constructor kwargs (all keyword-only)
EmojiPicker(
    categories: Sequence[str] | None = None,
    default_skin_tone: int = 1,
    max_emoji_version: float | None = 14.0,
    show_recent: bool = False,          # reserved, not yet functional
    persist_path: str | Path | None = None,
    name: str | None = None,
    id: str | None = None,
    classes: str | None = None,
)
```

`EmojiPickerScreen` is intentionally **not exported** from this package. Callers
write their own thin `ModalScreen` wrapper (the README shows exactly how). This
keeps the modal interaction model out of the library and gives callers full
control over presentation and dismiss behaviour.

---

## How the widget works

### Data pipeline

1. **`emoji.EMOJI_DATA`** (from the `emoji` PyPI package) is the source of truth
   for all emoji codepoints and their CLDR names. It is filtered to
   `status == fully_qualified` at module import time and stored in
   `_FULLY_QUALIFIED`.

2. **`_data/categories.json`** maps each fully-qualified codepoint to
   `{group, subgroup, order}`. It is generated once by
   `scripts/generate_categories.py` from the Unicode CLDR `emoji-test.txt`
   and committed. It provides canonical Unicode group membership and display
   order — data that is not in the `emoji` library itself.

3. At `EmojiPicker.__init__` time, `_build_emoji_list()` merges both sources:
   filters by `max_emoji_version`, removes toned variants (Fitzpatrick bases
   only), excludes the `Component` group, applies any `categories` filter, and
   sorts by `categories.json` order. The result is stored in `self._emoji_list`
   as `list[tuple[str, str]]` (codepoint, CLDR name). This is computed once per
   widget instance — never rebuilt after construction.

### Widget DOM structure

```
EmojiPicker (Widget)
  Vertical
    Input             #emoji-search
    Tabs              #category-tabs
      Tab             (one per Unicode group + "All")
    Grid              #emoji-grid
      Button …        (one per displayed emoji)
    Horizontal        #skin-tone-bar
      Label           #skin-tone-label
      Select          #skin-tone-select
```

### Grid updates (diff-based)

`_populate_grid(emoji_list)` never calls `remove_children()` followed by
`mount_all()` for the whole grid. Instead it:
1. Overwrites labels on existing buttons where they differ.
2. `mount_all()`s only the *new* buttons if the list grew.
3. Calls `remove()` only on the *excess* buttons if the list shrank.

This is critical for performance. A full remount of ~170 buttons causes
Textual to schedule N layout passes (one per `mount()` call) and produces
visible flicker on every keystroke. The diff approach limits DOM mutations to
the delta, which is typically zero after the initial population.

Do not change this to `remove_children() + mount_all()` even if it looks
simpler — it will regress rendering performance noticeably.

### Search (debounced)

`on_input_changed` cancels any pending `Timer` and schedules a new one for
150 ms. The timer calls `_populate_grid(_emoji_for_display(query, group))`.
The debounce prevents a grid rebuild on every keypress during fast typing.

### Category tabs

`_make_category_tabs()` is called at `compose()` time and yields one `Tab`
per Unicode group present in `_emoji_list` (filtered by `categories` kwarg),
plus an "All" tab appended at the end. The first category tab is
auto-activated by Textual's `Tabs` widget on mount, which triggers
`on_tabs_tab_activated` and populates the grid with only that category's
emoji. This is a deliberate performance choice: loading ~170 emoji for the
first tab is instant; loading all 1 800+ for "All" takes longer and is
deferred until the user explicitly switches to it.

### Skin tones

`_FITZPATRICK_MODIFIERS` contains the five Unicode modifier codepoints
(U+1F3FB–U+1F3FF). `_SKIN_TONE_CAPABLE` is a `frozenset` of base codepoints
that accept these modifiers, derived by scanning `emoji.EMOJI_DATA` for entries
with `_tone1`–`_tone5` variants.

`_apply_skin_tone(cp, modifier)` returns the modified form if `cp` is in
`_SKIN_TONE_CAPABLE` and `modifier` is non-empty, otherwise returns `cp`
unchanged. It is called when rendering each button label and again when posting
`EmojiSelected`.

The current modifier is stored in `self._skin_modifier` (a codepoint string or
empty string for neutral). When the user changes the tone via the `Select`
widget or a keyboard shortcut, `_save_skin_tone()` writes it to `persist_path`
(if set) and `_refresh_grid()` repopulates the grid.

---

## Emoji data file

**`_data/categories.json`** is committed and should not normally need
regeneration. If the Unicode Emoji version is bumped or the file is lost,
regenerate it:

```bash
uv run python scripts/generate_categories.py
```

The script fetches `https://unicode.org/Public/emoji/15.0/emoji-test.txt`,
parses group/subgroup headers, and writes `src/textual_emoji_picker/_data/categories.json`.
Commit the result. The file maps every fully-qualified codepoint to:

```json
{
  "😀": {"group": "Smileys & Emotion", "subgroup": "face-smiling", "order": 0},
  ...
}
```

`order` is the 0-based index of the emoji in `emoji-test.txt` and determines
display order within each category. Do not hand-edit this file.

---

## Tests

Tests live in `tests/` and are split into two tiers.

**Tier 1 — `test_data.py`** (no Textual, pure Python): validates data integrity.
These tests run in under a second and require no async runtime. They cover
things like: the emoji list is non-empty, all listed codepoints appear in
`emoji.EMOJI_DATA`, categories filter correctly, version filter works.

**Tier 2 — `test_widget.py`** (Textual pilot): exercises widget behaviour via
`app.run_test()`. These tests cover: grid is populated on mount, search
filters correctly, `EmojiSelected` is posted on click, `Cancelled` is posted
on Escape, skin tone is applied and not applied to incapable emoji.

Run the full suite:

```bash
uv run pytest
```

Run a single test:

```bash
uv run pytest tests/test_widget.py::test_skin_tone_applied
```

All tests must pass before merging any change. The CI matrix covers Python
3.11, 3.12, and 3.13.

### Writing new tests

- Widget tests use a host `App` that composes `EmojiPicker` and captures
  messages in instance attributes. See `PickerApp` in `test_widget.py` for
  the pattern.
- Always `await pilot.pause()` after mount and after interactions that trigger
  async callbacks or timers. For the 150 ms search debounce, use
  `await pilot.pause(delay=0.2)`.
- Do not test internal helpers directly (functions prefixed with `_`). Test
  observable widget behaviour only.

---

## Type checking

The package is `mypy --strict` clean. Run it as:

```bash
uv run mypy
```

`pyproject.toml` configures mypy to check only `src/` and `tests/` via the
`packages` and `mypy_path` settings. Do not add `# type: ignore` comments
without an explanatory note. The only accepted exception is the `float(raw)`
cast in `_emoji_version` where the `emoji` library's typing is incomplete.

---

## Linting and formatting

```bash
uv run ruff check .     # lint
uv run ruff format .    # format
```

Both are enforced in CI. `ruff format` uses the project's 100-character line
length. Do not configure exceptions to selected rules without discussion.

---

## Non-negotiables

These are hard constraints — do not work around them:

1. **No full grid remount on search or tone change.** Always use the diff-based
   `_populate_grid` pattern. See "Grid updates" above.

2. **No tooltips on emoji buttons.** Textual manages tooltips by mounting and
   removing a `Tooltip` widget on hover, which triggers layout recalculation
   on the whole screen for every button boundary the mouse crosses. With ~170
   buttons this causes continuous flicker. The emoji codepoint is visible in
   the button label; a tooltip is not necessary.

3. **`DEFAULT_CSS` only — no external `.tcss` files.** Library widgets must use
   inline `DEFAULT_CSS`. Shipping a `.tcss` file as package data is an
   anti-pattern because consumers would need to mount it manually.

4. **No runtime dependencies beyond `textual` and `emoji`.** The `emoji`
   package provides all needed Unicode data. Do not add `platformdirs` or any
   other dependency to this library — callers who need XDG paths can resolve
   `persist_path` themselves.

5. **`py.typed` must remain in both `py.typed` (repo root / sdist) and
   `src/textual_emoji_picker/py.typed` (wheel).** Removing either breaks PEP 561
   compliance.

---

## Versioning and changelog

This project follows [Semantic Versioning](https://semver.org/). The version is
set in `pyproject.toml` and mirrored in `src/textual_emoji_picker/__init__.py`.
Update both together.

The `CHANGELOG` section in `README.md` is the user-facing change log. Add an
entry for every release. GitHub Releases are generated automatically from the
publish workflow using `generate_release_notes: true`.

---

## Roadmap context

The roadmap is in `README.md` under "Feature comparison". When implementing a
roadmap item, keep this file and the README in sync. Short summary:

- **v0.2** — `show_recent` (in-memory recently-used category), column count
  reactive to widget width.
- **v0.3** — Disk persistence for recently-used (`platformdirs`), i18n via
  `emoji` locale data.
- **v0.4** — Custom emoji (`custom_emoji` kwarg), multi-keyword search.

Do not implement roadmap items ahead of schedule without opening an issue first.
Each item has downstream implications for the public API and the consuming apps
(e.g. telemente) that need to be considered before the interface is locked in.

---

## Release process

1. Update the version in `pyproject.toml` and `src/textual_emoji_picker/__init__.py`.
2. Add a changelog entry to `README.md`.
3. Commit: `git commit -m "release: v0.x.y"`.
4. Tag: `git tag v0.x.y && git push origin v0.x.y`.
5. The `publish.yaml` workflow builds the wheel and sdist, publishes to PyPI via
   Trusted Publishing (OIDC — no API key required), and creates a GitHub
   Release with auto-generated notes.

PyPI Trusted Publishing is configured at
`https://pypi.org/manage/account/publishing/` — the environment name is
`pypi`, the workflow file is `publish.yaml`.