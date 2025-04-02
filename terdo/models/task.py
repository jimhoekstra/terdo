from pathlib import Path
from pydantic import BaseModel, model_validator, ValidationError
from pydantic_core import PydanticCustomError
from datetime import datetime

from terdo.utils.io import (
    add_markdown_extension,
    get_root_markdown_dir,
    create_new_markdown_file,
    get_default_new_file_name,
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
    children = sorted(children, key=lambda x: x.last_edited, reverse=True)
    return children


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

            if self.n_subtasks == 0:
                # If the directory is empty, turn the directory into a file
                self._path_to_file.rename(
                    self.dir / add_markdown_extension(self.name)
                ).touch()
                full_dir_path.rmdir()
            else:
                return self

        # Hypothesis: the task is a file
        if add_markdown_extension(self.name) == INDEX_FILE_NAME:
            raise PydanticCustomError(
                "TaskInvalidName",
                "Task name cannot be the same as the index file name.",
            )
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

        # If the task is a directory, recursively get the last modified time of the latest subtask
        if self._is_directory:
            subtasks = self.children
            latest_modified_time = max(
                subtask.last_edited for subtask in subtasks
            )
            return latest_modified_time
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

    def rename(self, new_name: str) -> None:
        """Renames the task."""
        assert self._path_to_file is not None, "Path to file is not set."
        if self._is_directory:
            full_dir_path = self.dir / self.name
            full_dir_path.rename(self.dir / new_name).touch()
            self._path_to_file = full_dir_path / INDEX_FILE_NAME

        else:
            new_path = self.dir / add_markdown_extension(new_name)
            self._path_to_file.rename(new_path).touch()
            self._path_to_file = new_path

        self.name = new_name
    
    def move_to_dir(self, dir: Path) -> None:
        if self._is_directory:
            full_dir_path = self.dir / self.name
            full_dir_path.rename(dir / self.name)
            self.dir = dir

            self._path_to_file = self.dir / self.name / INDEX_FILE_NAME
            self._path_to_file.touch()
        else:
            assert self._path_to_file is not None, "Path to file is not set."
            new_path = dir / add_markdown_extension(self.name)
            self._path_to_file.rename(new_path).touch()
            self._path_to_file = new_path
            self.dir = dir

    def _change_into_dir(self) -> None:
        assert self._path_to_file is not None, "Path to file is not set."
        full_dir_path = self.dir / self.name

        if not self._is_directory:
            full_dir_path.mkdir()
            self._path_to_file.rename(full_dir_path / INDEX_FILE_NAME)

            self._is_directory = True
            self._path_to_file = full_dir_path / INDEX_FILE_NAME

    def create_subtask(self) -> None:
        """Creates a subtask in the task."""
        assert self._path_to_file is not None, "Path to file is not set."
        full_dir_path = self.dir / self.name

        self._change_into_dir()

        create_new_markdown_file(
            full_dir_path,
            get_default_new_file_name(full_dir_path),
        )

    def add_task_as_subtask(self, task: "Task") -> None:
        """Adds a task as a subtask of the current task."""
        assert self._path_to_file is not None, "Path to file is not set."
        full_dir_path = self.dir / self.name

        self._change_into_dir()

        # Move the task to the subtask directory
        task.move_to_dir(full_dir_path)
