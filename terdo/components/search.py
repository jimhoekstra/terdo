from textual.widgets import Input
from textual.message import Message
from textual.dom import DOMNode


class Search(Input):
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
