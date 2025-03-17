from pathlib import Path
from datetime import datetime

from models.task import Task


PATH_TO_MARKDOWN_DIR = Path.cwd() / "markdown"


def get_root_markdown_dir() -> Path:
    return PATH_TO_MARKDOWN_DIR


def file_path_to_task(file_path: Path) -> Task:
    """Build a Task object given a file path."""
    return Task(
        name=file_path.name.removesuffix(".md"),
        last_edited=datetime.fromtimestamp(file_path.stat().st_mtime),
    )


def order_tasks_by_last_edited(tasks: list[Task]) -> list[Task]:
    """Order by last edited timestamp, with most recently edited first."""
    return sorted(tasks, key=lambda x: x.last_edited.timestamp(), reverse=True)


def list_markdown_files_in_dir(dir: Path) -> list[Path]:
    """Returns the names of all markdown files in a given directory."""
    dir_contents = list(dir.iterdir())
    markdown_files = [
        item for item in dir_contents if item.is_file() and item.suffix == ".md"
    ]
    return markdown_files


def load_tasks_in_dir(dir: Path) -> list[Task]:
    """Loads all the tasks in a given directory and returns them as Task objects."""
    markdown_files = list_markdown_files_in_dir(dir)
    tasks = [file_path_to_task(file_path) for file_path in markdown_files]
    return order_tasks_by_last_edited(tasks)


def add_markdown_extension(file_name: str) -> str:
    MARKDOWN_EXTENSION = "md"
    return f"{file_name}.{MARKDOWN_EXTENSION}"


def get_default_new_file_name(dir: Path) -> str:
    """Returns a default name for a new file that doesn't exist yet in the directory."""

    def generate_candidate_name(default_name: str, counter: int) -> str:
        """Builds a candidate name given a default name and an incrementing counter."""
        return f"{default_name} {int(counter)}"

    DEFAULT_NAME: str = "New markdown file"
    markdown_files_in_dir = [
        file.name for file in list_markdown_files_in_dir(dir)
    ]

    counter = 0
    candidate_name = add_markdown_extension(
        generate_candidate_name(DEFAULT_NAME, counter)
    )
    while candidate_name in markdown_files_in_dir:
        counter += 1
        candidate_name = add_markdown_extension(
            generate_candidate_name(DEFAULT_NAME, counter)
        )

    return candidate_name


def create_new_markdown_file(dir: Path, name: str) -> Path:
    """Create an empty markdown file in given location and returns the path."""
    new_file_path = dir / name
    new_file_path.touch(exist_ok=False)
    return new_file_path


def rename_markdown_file(
    original_name: str, new_name: str, dir: Path = PATH_TO_MARKDOWN_DIR
) -> None:
    file = dir / add_markdown_extension(original_name)
    file.rename(dir / add_markdown_extension(new_name))
