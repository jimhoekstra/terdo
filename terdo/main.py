from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer
from textual.containers import VerticalScroll, Container
from textual.reactive import reactive
from textual import on

from models.task import Task
from components.task_overview import TaskList, TaskOverview
from components.note import Note


def load_tasks(dir: Path) -> list[Task]:
    return [
        Task(
            id=idx,
            name=str(file_name).split("/")[-1].removesuffix(".md"),
            last_edited=datetime.fromtimestamp(file_name.stat().st_mtime),
        )
        for idx, file_name in enumerate(dir.iterdir())
        if file_name.is_file() and file_name.suffix == ".md"
    ]


class Terdo(App):
    BINDINGS = [
        ("q", "quit", "Quit Terdo"),
    ]

    CSS_PATH = "styles.tcss"

    note_content: reactive[Path] = reactive(
        Path.cwd() / "markdown" / "Test file.md"
    )

    def compose(self) -> ComposeResult:
        """Returns the main UI layout.

        Returns:
            The composed UI layout structure
        """
        with Container():
            with VerticalScroll(id="task-list-container"):
                yield TaskOverview(id="task-list-search")

            yield Note(id="note-content")

        yield Footer()

    async def on_mount(self) -> None:
        # Load the tasks in the main markdown directory, and pass them to the task list element
        tasks = load_tasks(Path.cwd() / "markdown")
        task_list_component = self.query_one("#task-list-search", TaskOverview)
        await task_list_component.set_tasks(tasks)

        # Focus the task list so the user can immediately start navigating tasks
        task_list_component.focus()

    async def action_quit(self) -> None:
        """Exits the program by calling the exit method."""
        self.exit()

    async def watch_note_content(self) -> None:
        note = self.query_one("#note-content", Note)
        note.content = self.note_content

    @on(TaskList.Highlighted)
    def item_highlighted(self, event: TaskList.Highlighted) -> None:
        note = self.query_one("#note-content", Note)

        item = event.item
        if item is None:
            return

        item_name = item.name
        if item_name is None:
            return

        note.content = Path.cwd() / "markdown" / f"{item_name}.md"


if __name__ == "__main__":
    app = Terdo()
    app.run()
