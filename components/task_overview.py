from textual.app import ComposeResult
from textual.widgets import Input
from textual.widget import Widget
from textual import on

from models.task import Task
from components.new_task import NewTask
from components.search import Search
from components.task_list import TaskList


class TaskOverview(Widget):
    all_tasks: list[Task] = []

    BINDINGS = [
        ("s", "search_tasks", "Search Tasks"),
    ]

    def compose(self) -> ComposeResult:
        yield Search(
            placeholder="Search for tasks...",
            id="task-list-search-input",
        )
        yield NewTask(id="new-task-input", classes="hidden")
        yield TaskList(id="task-list")

    def on_mount(self) -> None:
        self.get_task_view_element().focus().set_index(0)

    async def set_tasks(self, tasks: list[Task]) -> None:
        task_view_element = self.get_task_view_element()
        task_view_element.clear()
        for task in tasks:
            await task_view_element.append_task(task)
        task_view_element.set_index(0)
        self.all_tasks = tasks

    @on(Search.Changed, "#task-list-search-input")
    async def search_task_trigger(self, event: Input.Changed) -> None:
        await self.search_tasks(event.value)

    async def search_tasks(self, search_term: str) -> None:
        relevant_tasks = [
            task for task in self.all_tasks if search_term.lower() in task.name.lower()
        ]
        task_view_element = self.get_task_view_element()
        task_view_element.clear()
        for task in relevant_tasks:
            await task_view_element.append_task(task)

        task_view_element.set_index(0)

    @on(Search.SearchCancelled, "#task-list-search-input")
    async def cancel_search(self, event: Search.SearchCancelled) -> None:
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
        return self.query_one("#task-list-search-input", Search)

    def get_task_view_element(self) -> TaskList:
        return self.query_one("#task-list", TaskList)
