from textual.app import ComposeResult
from textual.widgets import Checkbox, ListView, ListItem
from textual.reactive import reactive

from models.task import Task


class TaskList(ListView):
    tasks: reactive[list[Task]] = reactive([])

    def compose(self) -> ComposeResult:
        for task in self.tasks:
            yield Checkbox(task.name)

    def watch_tasks(self) -> None:
        self.clear()
        for task in self.tasks:
            self.append(ListItem(Checkbox(task.name)))
