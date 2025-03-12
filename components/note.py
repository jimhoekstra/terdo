from textual.app import ComposeResult
from textual.widgets import Markdown, TextArea
from textual.widget import Widget
from textual.reactive import reactive
from pathlib import Path


class Note(Widget):
    content: reactive[Path] = reactive(Path.cwd() / "markdown" / "Do groceries.md")
    can_focus = True

    BINDINGS = [
        ("e", "edit", "Edit"),
        ("ctrl+s", "save", "Save"),
        ("escape", "save", "Save"),
    ]

    def compose(self) -> ComposeResult:
        yield Markdown("", id="note-viewer")
        yield TextArea("", language="markdown", id="note-editor", classes="hidden")

    async def watch_content(self) -> None:
        await self.reload_content()

    async def reload_content(self) -> None:
        markdown_element = self.query_one("#note-viewer", Markdown)
        await markdown_element.load(self.content)

    async def action_edit(self) -> None:
        markdown_element = self.query_one("#note-viewer", Markdown)
        markdown_element.add_class("hidden")

        textarea_element = self.query_one("#note-editor", TextArea)
        textarea_element.remove_class("hidden")

        if textarea_element.text != self.content.read_text():
            textarea_element.text = self.content.read_text()
        textarea_element.focus()

    async def action_save(self) -> None:
        markdown_element = self.query_one("#note-viewer", Markdown)
        markdown_element.remove_class("hidden")

        textarea_element = self.query_one("#note-editor", TextArea)
        textarea_element.add_class("hidden")

        self.content.write_text(textarea_element.text)
        await self.reload_content()

        self.focus()
