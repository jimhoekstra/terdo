from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer
from textual.containers import VerticalScroll, Grid
from textual.reactive import reactive
from textual import on

from terdo.components.task_overview import TaskList, TaskOverview
from terdo.components.note import Note
from terdo.utils.io import get_root_markdown_dir
from terdo.models.task import load_tasks_in_dir


class Terdo(App):
    """The main application class for Terdo.

    This class is responsible for setting up the main UI layout and handling
    the application state.
    """

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
        # The main grid layout that shows the task list on the left of the screen,
        # and the note content or editor on the right.
        with Grid(id="main-container"):
            with VerticalScroll(id="task-list-container"):
                yield TaskOverview(
                    markdown_dir=self.markdown_dir, id="task-list-search"
                )

            # The Note element contains either a Markdown element showing the
            # contents of a note or a Textarea element in which the contents
            # can edited, depending on the state of the app.
            yield Note(id="note-content")

        # The footer shows which keybindings are allowed in which application state
        # TODO: make configurable whether to show the footer or not
        yield Footer()

    async def on_mount(self) -> None:
        """Sets up the app when the app is mounted."""
        await self.set_directory(self.markdown_dir)

    async def watch_markdown_dir(self) -> None:
        """Sets the directory shown in the app to the given directory when it changes."""
        await self.set_directory(self.markdown_dir)

    async def set_directory(
        self, markdown_dir: Path, focus_task_list: bool = True
    ) -> None:
        """Sets the directory shown in the app to the given directory.

        Parameters
        ----------
        markdown_dir
            The directory to show in the app.
        focus_task_list
            Whether to focus the task list after loading the tasks.
        """
        tasks = load_tasks_in_dir(markdown_dir)
        if len(tasks) == 0:
            if markdown_dir == get_root_markdown_dir():
                self.app.notify(
                    "No tasks found in the root directory.", severity="warning"
                )
            else:
                self.markdown_dir = markdown_dir.parent
            return
        task_overview_component = self.query_one(TaskOverview)
        task_overview_component.markdown_dir = self.markdown_dir
        await task_overview_component.set_tasks(tasks)

        if focus_task_list:
            task_list_component = task_overview_component.query_one(TaskList)
            task_list_component.focus()

    @on(TaskList.Highlighted)
    def load_note(self, event: TaskList.Highlighted) -> None:
        """Loads the note content for the selected task.

        Parameters
        ----------
        event
            The event containing the selected task.
        """
        note = self.query_one("#note-content", Note)

        item = event.item
        if item is None:
            return

        task = item.task_instance
        note.task_item = task

    @on(TaskList.Selected)
    def item_selected(self, event: TaskList.Highlighted) -> None:
        """Focuses the Note element when a task is selected."""
        note = self.query_one("#note-content", Note)
        note.focus()

    @on(TaskList.RerenderTaskList)
    async def rerender_from_task_list(self):
        """Reloads the task list when a task is added or removed."""
        # TODO: resolve duplication with rerender_from_note
        await self.set_directory(self.markdown_dir)

    @on(Note.RerenderTaskList)
    async def rerender_from_note(self):
        """Reloads the task list when the note is saved."""
        # TODO: resolve duplication with rerender_from_task_list
        await self.set_directory(self.markdown_dir)

    @on(TaskList.SetDirectory)
    async def set_directory_from_task_list(
        self, event: TaskList.SetDirectory
    ) -> None:
        self.markdown_dir = event.markdown_dir

    @on(TaskList.OpenParentDirectory)
    async def open_parent_directory(self) -> None:
        """Opens the parent directory of the current directory."""
        if self.markdown_dir == get_root_markdown_dir():
            self.app.notify(
                "Already at the root directory.", severity="warning"
            )
            return

        new_dir = self.markdown_dir.parent
        self.markdown_dir = new_dir

    async def action_quit(self) -> None:
        """Exits the program by calling the exit method."""
        self.exit()


if __name__ == "__main__":
    # Run the app if the script is executed
    app = Terdo()
    app.run()
