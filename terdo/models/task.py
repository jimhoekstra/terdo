from pathlib import Path
from pydantic import BaseModel
from datetime import datetime

from terdo.utils.io import list_markdown_dirs_in_dir, list_markdown_files_in_dir


class Task(BaseModel):
    name: str
    path: Path
    last_edited: datetime
    is_directory: bool

    @property
    def children_dir(self) -> Path:
        if self.is_directory:
            return self.path.parent
        else:
            raise ValueError(
                "Task that is not a directory cannot have children."
            )

    @property
    def current_dir(self) -> Path:
        if self.is_directory:
            return self.path.parent.parent
        else:
            return self.path.parent

    @property
    def parent_dir(self) -> Path:
        if self.is_directory:
            return self.path.parent.parent.parent
        else:
            return self.path.parent.parent

    @property
    def n_subtasks(self) -> int:
        """Returns the number of subtasks in the task."""
        if self.is_directory:
            return len(
                list_markdown_files_in_dir(self.children_dir)
                + list_markdown_dirs_in_dir(self.children_dir)
            )
        else:
            return 0
