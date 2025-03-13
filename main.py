from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer
from textual.containers import VerticalScroll, Container

from textual.reactive import reactive
from textual import on

from models.task import Task
from components.task_list import TaskList, TaskListSearch
from components.note import Note


tasks = [
    Task(id=1, name="Do groceries"),
    Task(id=2, name="Finish homework"),
]


class Terdo(App):
    BINDINGS = [
        ("q", "quit", "Quit Terdo"),
    ]

    CSS_PATH = "styles.tcss"

    tasks: reactive[list[Task]] = reactive([])
    note_content: reactive[Path] = reactive(Path.cwd() / "markdown" / "Do groceries.md")

    def compose(self) -> ComposeResult:
        with Container():
            with VerticalScroll(id="task-list-container"):
                yield TaskListSearch(id="task-list-search")

            yield Note(id="note-content")

        yield Footer()

    def on_mount(self) -> None:
        self.tasks = tasks
        self.note_content = Path.cwd() / "markdown" / "Do groceries.md"

        task_list_component = self.query_one("#task-list-search", TaskListSearch)
        task_list_component.focus()

    async def action_quit(self) -> None:
        self.exit()

    async def watch_tasks(self) -> None:
        task_list = self.query_one("#task-list-search", TaskListSearch)
        task_list.all_tasks = self.tasks

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
