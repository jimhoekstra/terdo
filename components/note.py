from textual.app import ComposeResult
from textual.widgets import Markdown, TextArea
from textual.widget import Widget
from textual.reactive import reactive
from pathlib import Path


class Note(Widget):
    content: reactive[Path] = reactive(Path.cwd() / "markdown" / "Do groceries.md")
    can_focus = True

    BINDINGS = [("e", "edit", "Edit")]

    def compose(self) -> ComposeResult:
        yield Markdown("", id="note-viewer")

    async def watch_content(self) -> None:
        markdown_element = self.query_one("#note-viewer", Markdown)
        await markdown_element.load(self.content)

    async def action_edit(self) -> None:
        self.remove_children()
        self.mount(
            TextArea(
                text=self.content.read_text(), language="markdown", id="note-editor"
            )
        )
