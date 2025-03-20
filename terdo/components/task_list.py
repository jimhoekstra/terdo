from pathlib import Path
from datetime import datetime

from textual.widget import Widget
from textual.widgets import Checkbox, ListView, ListItem, Label, Button, Input
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.app import ComposeResult
from textual.message import Message
from textual import on
from textual.events import Blur

from terdo.models.task import Task
from terdo.utils.io import (
    create_new_markdown_file,
    get_default_new_file_name,
    rename_markdown_file,
)


class ChangeNameInput(Input):
    note_name: str
    BINDINGS = [
        ("escape", "cancel_change_name", "Cancel Renaming"),
    ]

    class ChangeNameCancelled(Message):
        def __init__(
            self,
            sender: "ChangeNameInput",
            note_name: str,
            focus_list_view: bool,
        ) -> None:
            self.sender: "ChangeNameInput" = sender
            self.note_name: str = note_name
            self.focus_list_view: bool = focus_list_view
            super().__init__()

        @property
        def control(self) -> "ChangeNameInput":
            return self.sender

    class ConfirmChangeName(Message):
        def __init__(
            self, sender: "ChangeNameInput", original_name: str, new_name: str
        ) -> None:
            self.sender: "ChangeNameInput" = sender
            self.original_name: str = original_name
            self.new_name: str = new_name
            super().__init__()

    def __init__(self, note_name: str, **kwargs) -> None:
        self.note_name = note_name
        super().__init__(**kwargs)

    async def action_submit(self) -> None:
        self.post_message(
            self.ConfirmChangeName(self, self.note_name, self.value)
        )

    def action_cancel_change_name(self) -> None:
        self.post_message(self.ChangeNameCancelled(self, self.note_name, True))

    @on(Blur)
    def cancel_change_name(self) -> None:
        self.post_message(self.ChangeNameCancelled(self, self.note_name, False))


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


class TaskListItem(ListItem):
    task_name: str

    def __init__(self, task_name: str, *children: Widget, **kwargs) -> None:
        self.task_name = task_name
        super().__init__(*children, **kwargs)


class TaskList(ListView):
    class RerenderTaskList(Message):
        pass

    # TODO: figure out how to properly handle this so that the type checker
    # understands what's going on and the "type: ignore" comments can be removed
    class Highlighted(ListView.Highlighted):
        def __init__(
            self, list_view: "TaskList", item: TaskListItem | None
        ) -> None:
            super().__init__(list_view, item)
            self.list_view: "TaskList" = list_view  # type: ignore
            """The view that contains the item highlighted."""
            self.item: TaskListItem | None = item  # type: ignore
            """The highlighted item, if there is one highlighted."""

        @property
        def control(self) -> "TaskList":
            return self.list_view

    BINDINGS = [
        ("j", "cursor_down", "Next"),
        ("k", "cursor_up", "Previous"),
        ("d", "delete_task", "Delete"),
        ("n", "new_task", "New Task"),
        ("r", "rename_task", "Rename Task"),
    ]

    markdown_dir: Path

    def __init__(self, markdown_dir: Path, **kwargs) -> None:
        self.markdown_dir = markdown_dir
        super().__init__(**kwargs)

    async def append_task(self, task: Task) -> None:
        await self.append(
            TaskListItem(task.name, Checkbox(task.name), name=task.name)
        )

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

    @property
    def highlighted_child(self) -> TaskListItem | None:
        """The currently highlighted TaskListItem, or None if nothing is highlighted."""
        if self.index is not None and 0 <= self.index < len(self._nodes):
            list_item = self._nodes[self.index]
            assert isinstance(list_item, TaskListItem)
            return list_item
        else:
            return None

    def action_new_task(self) -> None:
        new_file_name = get_default_new_file_name(self.markdown_dir)
        create_new_markdown_file(self.markdown_dir, new_file_name)
        self.post_message(self.RerenderTaskList())

    def action_rename_task(self) -> None:
        highlighted = self.highlighted_child
        if highlighted is None:
            return

        name = highlighted.task_name
        if name is None:
            return

        highlighted.remove_children()

        new_input_element = ChangeNameInput(note_name=name, value=name)
        highlighted.mount(new_input_element)

        new_input_element.focus()

    @on(ChangeNameInput.ChangeNameCancelled)
    def cancel_rename_task(
        self, event: ChangeNameInput.ChangeNameCancelled
    ) -> None:
        input_element = event.sender
        list_item_element = input_element.query_ancestor(TaskListItem)
        list_item_element.remove_children()

        new_checkbox_element = Checkbox(event.note_name)
        list_item_element.mount(new_checkbox_element)

        if event.focus_list_view:
            list_view = list_item_element.query_ancestor(ListView)
            list_view.focus()

    @on(ChangeNameInput.ConfirmChangeName)
    def submit_rename_task(
        self, event: ChangeNameInput.ConfirmChangeName
    ) -> None:
        input_element = event.sender
        rename_markdown_file(event.original_name, event.new_name)

        list_item_element = input_element.query_ancestor(TaskListItem)
        list_item_element.task_name = event.new_name
        list_item_element.remove_children()

        new_checkbox_element = Checkbox(event.new_name)
        list_item_element.mount(new_checkbox_element)

        list_view = list_item_element.query_ancestor(ListView)
        list_view.focus()
