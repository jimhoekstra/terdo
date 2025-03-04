from textual.app import App, ComposeResult
from textual.widgets import Footer, Checkbox, Label, Input, ListView, ListItem
from textual.containers import VerticalScroll, Container
from textual.message import Message
from textual.reactive import reactive
from pydantic import BaseModel


class Task(BaseModel):
    id: int
    name: str


tasks = [
    Task(id=1, name="Do groceries"),
    Task(id=2, name="Finish homework"),
    Task(id=3, name="Call mom"),
    Task(id=4, name="Buy a new phone"),
]


class NewTask(Input):
    class TaskSubmitted(Message):
        def __init__(self, task: Task) -> None:
            self.task = task
            super().__init__()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        new_task = Task(id=len(tasks) + 1, name=event.value)
        self.post_message(self.TaskSubmitted(task=new_task))


class TaskList(ListView):
    tasks: reactive[list[Task]] = reactive([])

    def compose(self) -> ComposeResult:
        for task in self.tasks:
            yield Checkbox(task.name)

    def watch_tasks(self) -> None:
        self.clear()
        for task in self.tasks:
            self.append(ListItem(Checkbox(task.name)))


class Terdo(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    CSS_PATH = "main.tcss"

    tasks: reactive[list[Task]] = reactive([])

    def compose(self) -> ComposeResult:
        with Container():
            with VerticalScroll(id="task-list"):
                yield NewTask(placeholder="Add a new task...")
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

    def on_new_task_task_submitted(self, message: NewTask.TaskSubmitted) -> None:
        self.tasks = self.tasks + [message.task]


if __name__ == "__main__":
    app = Terdo()
    app.run()
