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

    async def append_task(self, task: Task) -> None:
        await self.append(ListItem(Checkbox(task.name), name=task.name))

    async def remove_task(self, task: Task) -> None:
        for idx, child in enumerate(self.children):
            if task.name == child.name:
                self.remove_items([idx])
                break

    def set_index(self, index: int) -> "TaskListView":
        self.index = index
        return self


class TaskList(Widget):
    all_tasks: list[Task] = []

    BINDINGS = [
        ("s", "search_tasks", "Search Tasks"),
    ]

    def compose(self) -> ComposeResult:
        yield TaskListSearch(
            placeholder="Search for tasks...",
            id="task-list-search-input",
        )
        yield NewTask(id="new-task-input", classes="hidden")
        yield TaskListView(id="task-list")

    def on_mount(self) -> None:
        self.get_task_view_element().focus().set_index(0)

    async def set_tasks(self, tasks: list[Task]) -> None:
        task_view_element = self.get_task_view_element()
        task_view_element.clear()
        for task in tasks:
            await task_view_element.append_task(task)
        task_view_element.set_index(0)
        self.all_tasks = tasks

    @on(TaskListSearch.Changed, "#task-list-search-input")
    async def search_task_trigger(self, event: Input.Changed) -> None:
        await self.search_tasks(event.value)
        
    async def search_tasks(self, search_term: str) -> None:
        relevant_tasks = [task for task in self.all_tasks if search_term.lower() in task.name.lower()]
        task_view_element = self.get_task_view_element()
        task_view_element.clear()
        for task in relevant_tasks:
            await task_view_element.append_task(task)    

        task_view_element.set_index(0)

    @on(TaskListSearch.SearchCancelled, "#task-list-search-input")
    async def cancel_search(self, event: TaskListSearch.SearchCancelled) -> None:
        task_view_element = self.get_task_view_element()
        task_view_element.clear()
        for task in self.all_tasks:
            await task_view_element.append_task(task)

        task_view_element.focus()
        task_view_element.set_index(0)

        self.get_search_input_element().clear()

    async def action_search_tasks(self) -> None:
        search_input_element = self.get_search_input_element()
        search_input_element.focus()

    def get_search_input_element(self) -> Input:
        return self.query_one("#task-list-search-input", TaskListSearch)

    def get_task_view_element(self) -> TaskListView:
        return self.query_one("#task-list", TaskListView)
