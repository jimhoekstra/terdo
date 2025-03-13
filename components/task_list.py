from textual.app import ComposeResult
from textual.widgets import Checkbox, ListView, ListItem, Input
from textual.widget import Widget
from textual.reactive import reactive
from textual import on

from models.task import Task


class TaskList(ListView):
    tasks: reactive[list[Task]] = reactive([])

    BINDINGS = [("j", "cursor_down", "Next"), ("k", "cursor_up", "Previous")]

    def compose(self) -> ComposeResult:
        for task in self.tasks:
            yield ListItem(Checkbox(task.name), name=task.name)

    async def watch_tasks(self) -> None:
        await self.recompose()
        self.index = 0


class TaskListSearch(Widget):
    all_tasks: reactive[list[Task]] = reactive([])
    displayed_tasks: reactive[list[Task]] = reactive([])

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search for tasks...", id="task-list-search-input")
        yield TaskList(id="task-list")

    def on_mount(self) -> None:
        task_list = self.query_one("#task-list", TaskList)
        task_list.focus()

    @on(Input.Changed, "#task-list-search-input")
    def search_tasks(self, event: Input.Changed) -> None:
        search_term = event.value
        self.displayed_tasks = [
            task for task in self.all_tasks if search_term.lower() in task.name.lower()
        ]

    async def watch_all_tasks(self) -> None:
        self.displayed_tasks = self.all_tasks

    async def watch_displayed_tasks(self) -> None:
        task_list = self.query_one("#task-list", TaskList)
        task_list.tasks = self.displayed_tasks
