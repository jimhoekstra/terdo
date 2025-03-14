from textual.widgets import Checkbox, ListView, ListItem

from models.task import Task


class TaskList(ListView):
    BINDINGS = [("j", "cursor_down", "Next"), ("k", "cursor_up", "Previous")]

    async def append_task(self, task: Task) -> None:
        await self.append(ListItem(Checkbox(task.name), name=task.name))

    async def remove_task(self, task: Task) -> None:
        for idx, child in enumerate(self.children):
            if task.name == child.name:
                self.remove_items([idx])
                break

    def set_index(self, index: int) -> "TaskList":
        self.index = index
        return self
