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
    tasks: reactive[list[Task]] = reactive([])

    BINDINGS = [("j", "cursor_down", "Next"), ("k", "cursor_up", "Previous")]

    def compose(self) -> ComposeResult:
        for task in self.tasks:
            yield ListItem(Checkbox(task.name), name=task.name)

    async def watch_tasks(self) -> None:
        await self.recompose()


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
        task_list = self.query_one("#task-list", TaskListView)
        task_list.focus()
        task_list.index = 0

    @on(TaskListSearch.Changed, "#task-list-search-input")
    def search_tasks(self, event: Input.Changed) -> None:
        search_term = event.value
        self.displayed_tasks = [
            task for task in self.all_tasks if search_term.lower() in task.name.lower()
        ]

    @on(TaskListSearch.SearchCancelled, "#task-list-search-input")
    def cancel_search(self, event: TaskListSearch.SearchCancelled) -> None:
        self.get_search_input_element().add_class("hidden")
        self.displayed_tasks = self.all_tasks

    async def action_search_tasks(self) -> None:
        self.get_search_input_element().remove_class("hidden").focus()

    async def watch_all_tasks(self) -> None:
        self.displayed_tasks = self.all_tasks

    async def watch_displayed_tasks(self) -> None:
        self.get_task_view_element().tasks = self.displayed_tasks

    def get_search_input_element(self) -> Input:
        return self.query_one("#task-list-search-input", TaskListSearch)

    def get_task_view_element(self) -> TaskListView:
        return self.query_one("#task-list", TaskListView)
