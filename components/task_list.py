from textual.app import ComposeResult
from textual.widgets import Checkbox, ListView, ListItem
from textual.reactive import reactive

from models.task import Task


class TaskList(ListView):
    tasks: reactive[list[Task]] = reactive([])

    BINDINGS = [("k", "cursor_up", "Up"), ("j", "cursor_down", "Down")]

    def compose(self) -> ComposeResult:
        for task in self.tasks:
            yield ListItem(Checkbox(task.name), name=task.name)

    async def watch_tasks(self) -> None:
        await self.recompose()
        self.index = 0
