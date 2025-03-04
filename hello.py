from textual.app import App, ComposeResult
from textual.widgets import Footer, Checkbox, Label, Input
from textual.containers import VerticalScroll, Container
from pydantic import BaseModel


class Task(BaseModel):
    id: int
    name: str


DUMMY_TASKS = [
    Task(id=1, name="Do groceries"),
    Task(id=2, name="Finish homework"),
    Task(id=3, name="Call mom"),
    Task(id=4, name="Buy a new phone"),
]


class Terdo(App): 

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    CSS_PATH = "main.tcss"

    def compose(self) -> ComposeResult:
        with Container():
            with VerticalScroll(id="task-list"):
                yield Input(placeholder="Search...")
                for task in DUMMY_TASKS:
                    yield Checkbox(task.name)
            with VerticalScroll(id="detail"):
                Label("Hello World")
        yield Footer()

    async def action_quit(self) -> None:
        self.exit()


if __name__ == "__main__":
    app = Terdo()
    app.run()
