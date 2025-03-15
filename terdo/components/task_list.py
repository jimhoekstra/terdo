from pathlib import Path

from textual.widgets import Checkbox, ListView, ListItem, Label, Button
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.app import ComposeResult
from textual import on

from models.task import Task


class DeleteTaskModal(ModalScreen[bool]):
    """Screen with a dialog to delete a task."""

    task_to_delete: Task

    def __init__(self, task_to_delete: Task, **kwargs) -> None:
        self.task_to_delete = task_to_delete
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to delete this task:", id="question"),
            Label(self.task_to_delete.name, id="task-to-delete"),
            Button("Delete", variant="error", id="delete"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    @on(Button.Pressed, "#cancel")
    def close_modal(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#delete")
    def confirm_delete(self) -> None:
        self.dismiss(True)


class TaskList(ListView):
    BINDINGS = [
        ("j", "cursor_down", "Next"),
        ("k", "cursor_up", "Previous"),
        ("d", "delete_task", "Delete"),
    ]

    async def append_task(self, task: Task) -> None:
        await self.append(ListItem(Checkbox(task.name), name=task.name))

    def set_index(self, index: int) -> "TaskList":
        self.index = index
        return self

    def action_delete_task(self) -> None:
        highlighted = self.highlighted_child
        if highlighted is None:
            return

        task_name = highlighted.name
        if task_name is None:
            return

        def confirm_delete(delete: bool | None) -> None:
            if delete:
                path_to_file = Path.cwd() / "markdown" / f"{task_name}.md"
                path_to_file.unlink()

        self.app.push_screen(
            DeleteTaskModal(Task(name=task_name, id=0)), confirm_delete
        )
