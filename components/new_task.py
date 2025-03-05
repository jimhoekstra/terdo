from textual.widgets import Input
from textual.message import Message
from textual import on

from models.task import Task


class NewTask(Input):
    class TaskSubmitted(Message):
        def __init__(self, task: Task) -> None:
            self.task = task
            super().__init__()

    @on(Input.Submitted)
    def submit_input(self, event: Input.Submitted) -> None:
        # TODO: give correct value for id
        new_task = Task(id=1, name=event.value)
        self.post_message(self.TaskSubmitted(task=new_task))
