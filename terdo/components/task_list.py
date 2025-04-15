from pathlib import Path

from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label, Button, Input
from textual.screen import ModalScreen
from textual.containers import Grid, Horizontal
from textual.app import ComposeResult
from textual.message import Message
from textual import on
from textual.events import Blur

from terdo.models.task import Task
from terdo.utils.io import (
    create_new_markdown_file,
    get_default_new_file_name,
    get_root_markdown_dir,
)


class ChangeNameInput(Input):
    task_instance: Task
    BINDINGS = [
        ("escape", "cancel_change_name", "Cancel Renaming"),
    ]

    class ChangeNameCancelled(Message):
        def __init__(
            self,
            sender: "ChangeNameInput",
            task_instance: Task,
            focus_list_view: bool,
        ) -> None:
            self.sender: "ChangeNameInput" = sender
            self.task_instance: Task = task_instance
            self.focus_list_view: bool = focus_list_view
            super().__init__()

        @property
        def control(self) -> "ChangeNameInput":
            return self.sender

    class ConfirmChangeName(Message):
        def __init__(
            self,
            sender: "ChangeNameInput",
        ) -> None:
            self.sender: "ChangeNameInput" = sender
            super().__init__()

        @property
        def control(self) -> "ChangeNameInput":
            return self.sender

    def __init__(self, task_instance: Task, **kwargs) -> None:
        self.task_instance = task_instance
        super().__init__(value=task_instance.name, **kwargs)

    async def action_submit(self) -> None:
        self.task_instance.rename(self.value)
        self.post_message(self.ConfirmChangeName(self))

    def action_cancel_change_name(self) -> None:
        self.post_message(
            self.ChangeNameCancelled(self, self.task_instance, True)
        )

    @on(Blur)
    def cancel_change_name(self) -> None:
        self.post_message(
            self.ChangeNameCancelled(self, self.task_instance, False)
        )


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
    task_instance: Task

    def __init__(self, task: Task, *children: Widget, **kwargs) -> None:
        self.task_instance = task
        super().__init__(*children, **kwargs)

    def set_task(self, task: Task) -> "TaskListItem":
        self.task_instance = task
        return self

    def set_task_name(self, task_name: str) -> "TaskListItem":
        self.task_instance.name = task_name
        return self


class TaskList(ListView):
    class RerenderTaskList(Message):
        def __init__(
            self, sender: "TaskList", rename_first_item: bool = False
        ) -> None:
            self.sender: "TaskList" = sender
            self.rename_first_item: bool = rename_first_item
            super().__init__()

        @property
        def control(self) -> "TaskList":
            return self.sender

    class SetDirectory(Message):
        def __init__(
            self,
            sender: "TaskList",
            markdown_dir: Path,
            rename_first_item: bool = False,
        ) -> None:
            self.sender: "TaskList" = sender
            self.markdown_dir: Path = markdown_dir
            self.rename_first_item: bool = rename_first_item
            super().__init__()

        @property
        def control(self) -> "TaskList":
            return self.sender

    class OpenParentDirectory(Message):
        pass

    # TODO: figure out how to properly handle this so that the type checker
    # understands what's going on and the "type: ignore" comments can be removed
    class Highlighted(ListView.Highlighted):
        def __init__(
            self, list_view: "TaskList", item: TaskListItem | None
        ) -> None:
            super().__init__(list_view, item)
            self.list_view: "TaskList" = list_view  # type: ignore
            self.item: TaskListItem | None = item  # type: ignore

        @property
        def control(self) -> "TaskList":
            return self.list_view

    BINDINGS = [
        ("j", "cursor_down", "Next"),
        ("k", "cursor_up", "Previous"),
        ("l", "open_children", "Subtasks"),
        ("h", "open_parent", "Parent"),
        ("d", "delete_task", "Delete"),
        ("n", "new_task", "New Task"),
        ("r", "rename_task", "Rename Task"),
        ("N", "new_subtask", "New Subtask"),
        ("m", "move_task", "Move Task"),
        ("M", "move_task_to", "Move Into"),
        ("P", "move_task_to_parent", "Move To Parent"),
        ("c", "cancel_action", "Cancel Action"),
    ]

    markdown_dir: Path
    task_to_move: Task | None

    def __init__(self, markdown_dir: Path, **kwargs) -> None:
        self.markdown_dir = markdown_dir
        self.task_to_move = None
        super().__init__(**kwargs)

    @staticmethod
    def _create_task_list_item_children(task: Task) -> Horizontal:
        labels = [Label(" "), Label(task.name)]
        n_subtasks = task.n_subtasks
        if n_subtasks > 0:
            labels.append(Label(f"({n_subtasks})", classes="task-info"))

        return Horizontal(*labels, classes="task-description")

    def _create_task_list_item(self, task: Task) -> TaskListItem:
        additional_classes = ""
        if self.task_to_move == task:
            additional_classes += " task-to-move"

        return TaskListItem(
            task,
            self._create_task_list_item_children(task),
            name=task.name,
            classes="task" + additional_classes,
        )

    async def append_task(self, task: Task) -> None:
        await self.append(
            self._create_task_list_item(task),
        )

    def set_index(self, index: int) -> "TaskList":
        self.index = index
        return self

    def action_open_children(self) -> None:
        highlighted = self.highlighted_child
        if highlighted is None:
            return

        if not highlighted.task_instance._is_directory:
            self.app.notify(
                "This task does not have any subtasks.", severity="warning"
            )
            return

        self.post_message(
            self.SetDirectory(self, highlighted.task_instance.path_to_children)
        )

    def action_open_parent(self) -> None:
        self.post_message(self.OpenParentDirectory())

    def action_delete_task(self) -> None:
        highlighted = self.highlighted_child
        if highlighted is None:
            return

        task = highlighted.task_instance

        def confirm_delete(delete: bool | None) -> None:
            if delete:
                task.delete()
                # Since we deleted a file, we want the main app to reload and
                # rerender the list of tasks that is shown to the user.
                self.post_message(self.RerenderTaskList(self))

        # Show the modal screen for confirming the delete action
        self.app.push_screen(
            DeleteTaskModal(task),
            # callback function that handles the users input in the modal
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
        self.post_message(self.RerenderTaskList(self, rename_first_item=True))

    def action_rename_task(self) -> None:
        highlighted = self.highlighted_child
        if highlighted is None:
            return

        task_instance = highlighted.task_instance
        highlighted.remove_children()

        new_input_element = ChangeNameInput(task_instance=task_instance)
        highlighted.mount(new_input_element)
        highlighted.remove_class("task").add_class("task-rename")

        new_input_element.focus()

    @on(ChangeNameInput.ChangeNameCancelled)
    def cancel_rename_task(
        self, event: ChangeNameInput.ChangeNameCancelled
    ) -> None:
        input_element = event.sender
        list_item_element = input_element.query_ancestor(TaskListItem)

        list_item_element.remove_children()
        list_item_element.mount(
            self._create_task_list_item_children(event.task_instance)
        )
        list_item_element.add_class("task").remove_class("task-rename")

        if event.focus_list_view:
            list_view = list_item_element.query_ancestor(ListView)
            list_view.focus()

    @on(ChangeNameInput.ConfirmChangeName)
    def submit_rename_task(
        self, event: ChangeNameInput.ConfirmChangeName
    ) -> None:
        self.post_message(self.RerenderTaskList(self))

    def action_new_subtask(self) -> None:
        highlighted = self.highlighted_child
        if highlighted is None:
            return

        task = highlighted.task_instance

        task.create_subtask()
        self.post_message(
            self.SetDirectory(
                self, task.path_to_children, rename_first_item=True
            )
        )

    def action_move_task(self) -> None:
        highlighted = self.highlighted_child
        if highlighted is None:
            return

        highlighted.add_class("task-to-move")

        task = highlighted.task_instance
        self.task_to_move = task
        self.app.notify(
            task.name,
            title="Selected for moving:",
        )

    def action_move_task_to(self) -> None:
        highlighted = self.highlighted_child
        if highlighted is None:
            return

        if self.task_to_move is None:
            self.app.notify(
                "No task selected for moving.",
                severity="warning",
            )
            return

        target_task = highlighted.task_instance
        target_task.add_task_as_subtask(self.task_to_move)
        self.post_message(self.SetDirectory(self, target_task.path_to_children))
        self.task_to_move = None

    def action_move_task_to_parent(self):
        highlighted = self.highlighted_child
        if highlighted is None:
            return

        if self.task_to_move is None:
            self.app.notify(
                "No task selected for moving.",
                severity="warning",
            )
            return

        if self.task_to_move.dir == get_root_markdown_dir():
            self.app.notify(
                "Cannot move to parent directory of the root markdown directory.",
                severity="warning",
            )
            return

        self.task_to_move.move_to_dir(self.task_to_move.path_to_parent)
        self.post_message(self.SetDirectory(self, self.task_to_move.dir))
        self.task_to_move = None

    def action_cancel_action(self) -> None:
        task_to_move = self.task_to_move
        if task_to_move is not None:
            self.task_to_move = None
            self.post_message(self.RerenderTaskList(self))
            self.notify(
                task_to_move.name,
                title="Cancelled moving task.",
            )
        else:
            self.app.notify(
                "No action currently enabled.",
                severity="warning",
            )
