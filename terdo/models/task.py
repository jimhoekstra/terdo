from pathlib import Path
from pydantic import BaseModel, model_validator, ValidationError
from pydantic_core import PydanticCustomError
from datetime import datetime

from terdo.utils.io import (
    add_markdown_extension,
    get_root_markdown_dir,
)


INDEX_FILE_NAME = add_markdown_extension("_index")


def load_tasks_in_dir(dir: Path) -> list["Task"]:
    children: list["Task"] = []
    for file_or_dir in dir.iterdir():
        try:
            children.append(
                Task(
                    name=file_or_dir.name,
                    dir=dir,
                )
            )
        except ValidationError:
            # Ignore files that are not tasks
            pass
    return sorted(children, key=lambda x: x.last_edited, reverse=True)


class Task(BaseModel):
    name: str
    dir: Path

    _is_directory: bool | None = None
    _path_to_file: Path | None = None

    @model_validator(mode="after")
    def _validate_path(self) -> "Task":
        
        self.name = self.name.removesuffix(".md")

        # Hypothesis: the task is a directory that contains subtasks
        full_dir_path = self.dir / self.name

        if (
            full_dir_path.exists()
            and full_dir_path.is_dir()
            and (full_dir_path / INDEX_FILE_NAME).exists()
        ):
            self._is_directory = True
            self._path_to_file = full_dir_path / INDEX_FILE_NAME
            return self

        # Hypothesis: the task is a file
        full_file_path = self.dir / add_markdown_extension(self.name)

        if full_file_path.exists() and full_file_path.is_file():
            self._is_directory = False
            self._path_to_file = full_file_path
            return self

        # If neither hypothesis is true, raise an error
        raise PydanticCustomError(
            "TaskDoesNotExist",
            "File {name} in directory {dir} is not a valid task.",
            {"name": self.name, "dir": self.dir},
        )
    
    @property
    def last_edited(self) -> datetime:
        """Returns the last edited time of the task."""
        assert self._path_to_file is not None, "Path to file is not set."
        return datetime.fromtimestamp(self._path_to_file.stat().st_mtime)

    @property
    def content(self) -> str:
        """Returns the content of the task."""
        assert self._path_to_file is not None, "Path to file is not set."
        return self._path_to_file.read_text()

    @property
    def path_to_parent(self) -> Path:
        """Returns the path to the parent directory of the task."""
        if self.dir == get_root_markdown_dir():
            raise ValueError(
                "Cannot get parent directory of the root markdown directory."
            )
        return self.dir.parent
    
    @property
    def path_to_children(self) -> Path:
        """Returns the path to the directory containing the subtasks."""
        if self._is_directory:
            return self.dir / self.name
        else:
            raise ValueError("Task is not a directory.")
    
    @property
    def children(self) -> list["Task"]:
        if self._is_directory:
            return load_tasks_in_dir(self.dir / self.name)
        else:
            return []            

    @property
    def n_subtasks(self) -> int:
        """Returns the number of subtasks in the task."""
        return len(self.children)
    
    def write(self, content: str) -> None:
        """Writes the content to the task."""
        assert self._path_to_file is not None, "Path to file is not set."
        self._path_to_file.write_text(content)

    def delete(self) -> None:
        """Deletes the task."""
        assert self._path_to_file is not None, "Path to file is not set."
        self._path_to_file.unlink()
