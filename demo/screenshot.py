"""Generate SVG screenshots of the EmojiPicker in various states.

Usage:
    uv run python demo/screenshot.py

Outputs SVG files into demo/screenshots/.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult

from textual_emoji_picker import EmojiPicker

OUT_DIR = Path(__file__).parent / "screenshots"


class ScreenshotApp(App[None]):
    """Headless app for capturing SVG screenshots."""

    CSS = """
    Screen {
        align: center middle;
        background: $surface;
    }
    """

    def __init__(self, **picker_kwargs: object) -> None:
        super().__init__()
        self._picker_kwargs = picker_kwargs

    def compose(self) -> ComposeResult:
        yield EmojiPicker(**self._picker_kwargs)  # type: ignore[arg-type]


async def capture(filename: str, **picker_kwargs: object) -> None:
    app = ScreenshotApp(**picker_kwargs)
    async with app.run_test(size=(60, 24)) as pilot:
        await pilot.pause()
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        app.save_screenshot(filename=filename, path=str(OUT_DIR))


async def main() -> None:
    await capture("default.svg")
    await capture("smileys-only.svg", categories=["smileys-emotion"])
    await capture("all-emoji.svg", max_emoji_version=None)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
