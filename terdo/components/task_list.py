from pathlib import Path
from datetime import datetime

from textual.widgets import Checkbox, ListView, ListItem, Label, Button
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.app import ComposeResult
from textual.message import Message
from textual import on

from models.task import Task
from utils.io import create_new_markdown_file, get_default_new_file_name


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
            Button("Cancel", variant="primary", id="cancel"),
            Button("Delete", variant="error", id="delete"),
            id="dialog",
        )

    @on(Button.Pressed, "#cancel")
    def close_modal(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#delete")
    def confirm_delete(self) -> None:
        self.dismiss(True)


class TaskList(ListView):
    class RerenderTaskList(Message):
        pass

    BINDINGS = [
        ("j", "cursor_down", "Next"),
        ("k", "cursor_up", "Previous"),
        ("d", "delete_task", "Delete"),
        ("n", "new_task", "New Task"),
    ]

    markdown_dir: Path

    def __init__(self, markdown_dir: Path, **kwargs) -> None:
        self.markdown_dir = markdown_dir
        super().__init__(**kwargs)

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

                # Since we deleted a file, we want the main app to reload and
                # rerender the list of tasks that is shown to the user.
                self.post_message(self.RerenderTaskList())

        # Show the modal screen for confirming the delete action
        self.app.push_screen(
            DeleteTaskModal(Task(name=task_name, last_edited=datetime.now())),
            # callback function that handles the user's input in the modal
            confirm_delete,
        )

    def action_new_task(self) -> None:
        # TODO: create new task in current directory
        new_file_name = get_default_new_file_name(self.markdown_dir)
        create_new_markdown_file(self.markdown_dir, new_file_name)
        self.post_message(self.RerenderTaskList())
