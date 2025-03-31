from textual.app import ComposeResult
from textual.widgets import Markdown, TextArea
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from textual import on
from terdo.models.task import Task
from terdo.utils.io import get_root_markdown_dir


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


class VimVerticalScroll(VerticalScroll):
    """A subclass of VerticalScroll that adds some Vim keybindngs to the keyboard controls."""

    BINDINGS = [
        ("j", "scroll_down", "Scroll Down"),
        ("k", "scroll_up", "Scroll Up"),
    ]


class Note(Widget):
    task_item: reactive[Task] = reactive(Task(name="Test file", dir=get_root_markdown_dir()))
    
    can_focus = False
    can_focus_children = True

    BINDINGS = [
        ("e", "edit", "Edit"),
    ]

    class RerenderTaskList(Message):
        pass

    def compose(self) -> ComposeResult:
        with VimVerticalScroll(
            can_focus=True,
            can_focus_children=False,
            can_maximize=True,
            id="note-viewer-container",
        ):
            yield Markdown("", id="note-viewer")
        yield NoteEditor(
            "",
            language="markdown",
            id="note-editor",
            classes="hidden",
            show_line_numbers=True,
        )

    async def watch_task_item(self) -> None:
        await self.reload_content()

    async def reload_content(self) -> None:
        markdown_element = self.query_one("#note-viewer", Markdown)
        await markdown_element.update(self.task_item.content)

    async def action_edit(self) -> None:
        # Hide the markdown element
        markdown_element = self.query_one(
            "#note-viewer-container", VimVerticalScroll
        )
        markdown_element.add_class("hidden")

        # Show the textarea element
        textarea_element = self.query_one("#note-editor", TextArea)
        textarea_element.remove_class("hidden")

        # Load the content of the markdown note into the textarea element
        if textarea_element.text != self.task_item.content:
            textarea_element.text = self.task_item.content

        # Set the cursor to the end of the text. TODO: make it more flexible
        # to place the cursor where the user wants it.
        lines = self.task_item.content.split("\n")
        num_lines = len(lines)
        num_chars_in_last_line = len(lines[-1])
        textarea_element.cursor_location = (
            num_lines - 1,
            num_chars_in_last_line,
        )
        textarea_element.insert(" ")

        # Lastly, focus the textarea element so that the user can start typing
        # immediately.
        textarea_element.focus()

    @on(NoteEditor.Save, "#note-editor")
    async def save(self, event: NoteEditor.Save) -> None:
        textarea_element = self.query_one("#note-editor", TextArea)
        self.task_item.write(textarea_element.text.strip())

        if not event.close_editor:
            # When only saving but not closing the editor, we want to
            # display a notification so that the user has a visual
            # confirmation that the note was saved.
            self.app.notify("Note saved successfully!")

        if event.close_editor:
            # Hide the textarea element, and show the markdown element again
            markdown_element = self.query_one(
                "#note-viewer-container", VimVerticalScroll
            )
            markdown_element.remove_class("hidden")
            textarea_element.add_class("hidden")

            # Reload the task list, because that is ordered by the last
            # modified date of the note. This is needed because the
            # markdown file was modified, and the task list needs to be
            # updated to reflect that.
            self.post_message(self.RerenderTaskList())
            await self.reload_content()
