from textual.widgets import Markdown
from textual.reactive import reactive
from pathlib import Path


class Note(Markdown):
    content: reactive[Path] = reactive(Path.cwd() / "markdown" / "Do groceries.md")
    can_focus = True

    async def watch_content(self) -> None:
        await self.load(self.content)
