from textual.app import ComposeResult
from textual.widgets import Markdown, TextArea
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from textual import on
from pathlib import Path


class NoteEditor(TextArea):

    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("escape", "close", "Close editor"),
    ]

    class Save(Message):

        sender: "NoteEditor"
        close_editor: bool

        def __init__(self, sender: "NoteEditor", close_editor: bool) -> None:
            self.sender = sender
            self.close_editor = close_editor
            super().__init__()
        
        @property
        def control(self) -> "NoteEditor":
            return self.sender

    async def action_save(self) -> None:
        self.post_message(self.Save(self, False))

    async def action_close(self) -> None:
        self.post_message(self.Save(self, True))


class Note(Widget):
    content: reactive[Path] = reactive(Path.cwd() / "markdown" / "Test file.md")
    can_focus = False
    can_focus_children = True

    BINDINGS = [
        ("e", "edit", "Edit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(can_focus=True, can_focus_children=False, can_maximize=True, id="note-viewer-container"):
            yield Markdown("", id="note-viewer")
        yield NoteEditor(
            "",
            language="markdown",
            id="note-editor",
            classes="hidden",
            show_line_numbers=True,
        )

    async def watch_content(self) -> None:
        await self.reload_content()

    async def reload_content(self) -> None:
        markdown_element = self.query_one("#note-viewer", Markdown)
        await markdown_element.load(self.content)

    async def action_edit(self) -> None:
        markdown_element = self.query_one("#note-viewer-container", VerticalScroll)
        markdown_element.add_class("hidden")

        textarea_element = self.query_one("#note-editor", TextArea)
        textarea_element.remove_class("hidden")

        markdown_text = self.content.read_text()
        if textarea_element.text != markdown_text:
            textarea_element.text = markdown_text

        lines = markdown_text.split("\n")
        num_lines = len(lines)
        num_chars_in_last_line = len(lines[-1])
        textarea_element.cursor_location = (
            num_lines - 1,
            num_chars_in_last_line,
        )
        textarea_element.insert(" ")

        textarea_element.focus()
    
    @on(NoteEditor.Save, "#note-editor")
    async def save(self, event: NoteEditor.Save) -> None:

        textarea_element = self.query_one("#note-editor", TextArea)
        self.content.write_text(textarea_element.text.strip())
        
        if not event.close_editor:
            self.app.notify("Note saved successfully!")
        
        if event.close_editor:
            markdown_element = self.query_one("#note-viewer-container", VerticalScroll)
            markdown_element.remove_class("hidden")
            textarea_element.add_class("hidden")

            await self.reload_content()
            self.focus()
