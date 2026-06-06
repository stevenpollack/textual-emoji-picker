"""Standalone demo app for textual-emoji-picker."""

from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Static
from textual import work

from textual_emoji_picker import EmojiPicker


class EmojiPickerScreen(ModalScreen[str]):
    """Modal wrapper that dismisses with the chosen emoji."""

    DEFAULT_CSS = """
    EmojiPickerScreen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield EmojiPicker()

    def on_emoji_picker_emoji_selected(self, event: EmojiPicker.EmojiSelected) -> None:
        self.dismiss(event.emoji)

    def on_emoji_picker_cancelled(self, event: EmojiPicker.Cancelled) -> None:
        self.dismiss("")


class DemoApp(App[None]):
    """Demo app showcasing the EmojiPicker widget."""

    TITLE = "textual-emoji-picker demo"
    CSS = """
    #picked {
        text-align: center;
        width: 1fr;
        height: 1fr;
        content-align: center middle;
    }
    """
    BINDINGS = [("e", "pick_emoji", "Pick Emoji")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Press [b]e[/b] to open the emoji picker", id="picked")
        yield Footer()

    @work
    async def action_pick_emoji(self) -> None:
        emoji = await self.push_screen_wait(EmojiPickerScreen())
        if emoji:
            self.query_one("#picked", Static).update(f"You picked: {emoji}")


if __name__ == "__main__":
    DemoApp().run()
