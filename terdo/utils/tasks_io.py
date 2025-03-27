from pathlib import Path
from datetime import datetime

from terdo.models.task import Task
from terdo.utils.io import (
    list_markdown_files_in_dir,
    list_markdown_dirs_in_dir,
)


def file_path_to_task(file_path: Path) -> Task:
    """Build a Task object given a file path."""
    return Task(
        name=file_path.name.removesuffix(".md"),
        path=file_path,
        last_edited=datetime.fromtimestamp(file_path.stat().st_mtime),
        is_directory=False,
    )


def markdown_dir_to_task(dir_path: Path) -> Task:
    return Task(
        name=dir_path.name,
        path=dir_path / "_index.md",
        # TODO: Check whether this is the correct way to get the last edited time of a directory
        last_edited=datetime.fromtimestamp(dir_path.stat().st_mtime),
        is_directory=True,
    )


def order_tasks_by_last_edited(tasks: list[Task]) -> list[Task]:
    """Order by last edited timestamp, with most recently edited first."""
    return sorted(tasks, key=lambda x: x.last_edited.timestamp(), reverse=True)


def load_tasks_in_dir(dir: Path) -> list[Task]:
    """Loads all the tasks in a given directory and returns them as Task objects."""
    markdown_files = list_markdown_files_in_dir(dir)
    markdown_dirs = list_markdown_dirs_in_dir(dir)

    tasks = [file_path_to_task(file_path) for file_path in markdown_files] + [
        markdown_dir_to_task(dir_path) for dir_path in markdown_dirs
    ]
    return order_tasks_by_last_edited(tasks)
