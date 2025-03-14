from textual.app import ComposeResult
from textual.widgets import Checkbox, ListView, ListItem, Input
from textual.widget import Widget
from textual.reactive import reactive
from textual import on
from textual.message import Message
from textual.dom import DOMNode

from models.task import Task
from components.new_task import NewTask


class TaskListSearch(Input):
    BINDINGS = [
        ("escape", "cancel_search", "Cancel"),
    ]

    class SearchCancelled(Message):
        def __init__(self, sender: DOMNode) -> None:
            self.sender: DOMNode = sender
            super().__init__()

        @property
        def control(self) -> DOMNode:
            return self.sender

    def action_cancel_search(self) -> None:
        self.post_message(self.SearchCancelled(sender=self))


class TaskListView(ListView):
    BINDINGS = [("j", "cursor_down", "Next"), ("k", "cursor_up", "Previous")]

    def append_task(self, task: Task) -> None:
        self.append(ListItem(Checkbox(task.name), name=task.name))

    def set_index(self, index: int) -> "TaskListView":
        self.index = index
        return self


class TaskList(Widget):
    all_tasks: reactive[list[Task]] = reactive([])
    displayed_tasks: reactive[list[Task]] = reactive([])

    BINDINGS = [
        ("s", "search_tasks", "Search Tasks"),
    ]

    def compose(self) -> ComposeResult:
        yield TaskListSearch(
            placeholder="Search for tasks...",
            id="task-list-search-input",
            classes="hidden",
        )
        yield NewTask(id="new-task-input", classes="hidden")
        yield TaskListView(id="task-list")

    def on_mount(self) -> None:
        self.get_task_view_element().focus().set_index(0)

    def append_tasks(self, tasks: list[Task]) -> None:
        task_view_element = self.get_task_view_element()
        for task in tasks:
            task_view_element.append_task(task)
        task_view_element.set_index(0)

    @on(TaskListSearch.Changed, "#task-list-search-input")
    def search_tasks(self, event: Input.Changed) -> None:
        search_term = event.value

        # Query all tasks in the task view
        task_items = self.get_task_view_element().query_children(ListItem)

        for task_item in task_items:
            task_item_name = task_item.name
            if task_item_name is None:
                continue

            # Make sure that items matching the query are shown
            if search_term.lower() in task_item_name.lower():
                task_item.remove_class("hidden")

            # Hide items that don't match the query
            else:
                task_item.add_class("hidden")

    @on(TaskListSearch.SearchCancelled, "#task-list-search-input")
    def cancel_search(self, event: TaskListSearch.SearchCancelled) -> None:
        self.get_search_input_element().add_class("hidden")

        # Make sure all tasks are visible
        task_items = self.get_task_view_element().query_children(ListItem)
        for task_item in task_items:
            task_item.remove_class("hidden")

    async def action_search_tasks(self) -> None:
        self.get_search_input_element().remove_class("hidden").focus()

    def get_search_input_element(self) -> Input:
        return self.query_one("#task-list-search-input", TaskListSearch)

    def get_task_view_element(self) -> TaskListView:
        return self.query_one("#task-list", TaskListView)
