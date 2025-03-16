from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Label
from textual.containers import VerticalScroll, Horizontal, Grid
from textual.reactive import reactive
from textual import on

from components.task_overview import TaskList, TaskOverview
from components.note import Note
from utils.io import load_tasks_in_dir, get_root_markdown_dir


class Terdo(App):
    BINDINGS = [
        ("q", "quit", "Quit Terdo"),
    ]

    CSS_PATH = "styles.tcss"
    markdown_dir: reactive[Path] = reactive(get_root_markdown_dir())

    def compose(self) -> ComposeResult:
        """Compose the main UI layout.

        Returns:
            The composed UI layout structure
        """
        yield Horizontal(
            Label("Path: "),
            Label("root", classes="path"),
            Label(" / "),
            Label("example", classes="path"),
            Label(" / "),
            Label("path", classes="path"),
            id="path-label",
        )
        with Grid(id="main-container"):
            with VerticalScroll(id="task-list-container"):
                yield TaskOverview(
                    markdown_dir=self.markdown_dir, id="task-list-search"
                )

            # The Note element contains either a Markdown element showing the
            # contents of a note or a Textarea element in which the contents
            # can edited, depending on the state of the app.
            yield Note(id="note-content")

        # yield Footer()

    async def on_mount(self) -> None:
        await self.set_directory(self.markdown_dir)

    async def watch_markdown_dir(self) -> None:
        await self.set_directory(self.markdown_dir)

    async def set_directory(
        self, markdown_dir: Path, focus_task_list: bool = True
    ) -> None:
        tasks = load_tasks_in_dir(markdown_dir)
        task_list_component = self.query_one(TaskOverview)
        task_list_component.markdown_dir = self.markdown_dir
        await task_list_component.set_tasks(tasks)

        if focus_task_list:
            task_list_component.focus()

    @on(TaskList.Highlighted)
    def item_highlighted(self, event: TaskList.Highlighted) -> None:
        note = self.query_one("#note-content", Note)

        item = event.item
        if item is None:
            return

        item_name = item.name
        if item_name is None:
            return

        note.content = Path.cwd() / "markdown" / f"{item_name}.md"

    @on(TaskList.Selected)
    def item_selected(self, event: TaskList.Highlighted) -> None:
        note = self.query_one("#note-content", Note)
        note.focus()

    @on(TaskList.RerenderTaskList)
    async def rerender_task_list(self):
        await self.set_directory(self.markdown_dir)

    async def action_quit(self) -> None:
        """Exits the program by calling the exit method."""
        self.exit()


if __name__ == "__main__":
    app = Terdo()
    app.run()
