from textual.app import App, ComposeResult
from textual.widgets import Footer, Label
from textual.containers import VerticalScroll, Container

from textual.reactive import reactive
from textual import on

from models.task import Task
from components.task_list import TaskList
from components.new_task import NewTask


tasks = [
    Task(id=1, name="Do groceries"),
    Task(id=2, name="Finish homework"),
    Task(id=3, name="Call mom"),
    Task(id=4, name="Buy a new phone"),
]


class Terdo(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    CSS_PATH = "main.tcss"

    tasks: reactive[list[Task]] = reactive([])

    def compose(self) -> ComposeResult:
        with Container():
            with VerticalScroll(id="task-list-container"):
                yield NewTask(id="new-task", placeholder="Add a new task...")
                yield TaskList(id="task-list")

            with VerticalScroll(id="detail"):
                Label("Hello World")

        yield Footer()

    def on_mount(self) -> None:
        self.tasks = tasks

    async def action_quit(self) -> None:
        self.exit()

    async def watch_tasks(self) -> None:
        task_list = self.query_one("#task-list", TaskList)
        task_list.tasks = self.tasks

    @on(NewTask.TaskSubmitted)
    def submit_task(self, message: NewTask.TaskSubmitted) -> None:
        self.tasks = self.tasks + [message.task]


if __name__ == "__main__":
    app = Terdo()
    app.run()
