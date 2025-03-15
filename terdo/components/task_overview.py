from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Input
from textual.widget import Widget
from textual.reactive import reactive
from textual import on

from models.task import Task
from components.search import Search
from components.task_list import TaskList


class TaskOverview(Widget):
    all_tasks: list[Task] = []
    markdown_dir: reactive[Path]

    BINDINGS = [
        ("s", "search_tasks", "Search Tasks"),
        ("n", "new_task", "New Tasks"),
    ]

    def __init__(self, markdown_dir: Path, **kwargs) -> None:
        self.markdown_dir = markdown_dir
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Search(
            placeholder="Search for tasks...",
            id="task-list-search-input",
        )
        yield TaskList(markdown_dir=self.markdown_dir, id="task-list")

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

    @on(Search.Submitted, "#task-list-search-input")
    async def search_submit_trigger(self, event: Input.Submitted) -> None:
        self.get_task_view_element().focus().set_index(0)

    async def search_tasks(self, search_term: str) -> None:
        relevant_tasks = [
            task
            for task in self.all_tasks
            if search_term.lower() in task.name.lower()
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

    async def watch_markdown_dir(self) -> None:
        self.get_task_view_element().markdown_dir = self.markdown_dir

    def get_search_input_element(self) -> Input:
        return self.query_one("#task-list-search-input", Search)

    def get_task_view_element(self) -> TaskList:
        return self.query_one("#task-list", TaskList)
