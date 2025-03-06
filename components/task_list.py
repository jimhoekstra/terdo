from textual.app import ComposeResult
from textual.widgets import Checkbox
from textual.reactive import reactive
from textual.containers import VerticalScroll

from models.task import Task


class TaskList(VerticalScroll):
    tasks: reactive[list[Task]] = reactive([])

    def compose(self) -> ComposeResult:
        for task in self.tasks:
            yield Checkbox(task.name)

    async def watch_tasks(self) -> None:
        await self.recompose()
