from pathlib import Path
from typing import List, Iterable, Union

__all__ = [
    "get_dir",
    "get_root_dir",
]


def get_root_dir(path: str | Path = None, **kwargs):
    match_first_git_dir: bool = kwargs.setdefault("match_first_git_dir", False)
    expected_root_names: Union[str, Path, List[Union[str, Path]]] = kwargs.setdefault("expected_root_names", [])

    if path is None:
        path = Path(__file__).parent.absolute()

    if not isinstance(path, Path):
        path = Path(path).absolute()

    if not path.exists():
        raise ValueError("Invalid Path: %r" % path)

    if not path.is_dir():
        directory = path.parent.absolute()

    else:
        directory = path.absolute()

    if match_first_git_dir:
        git_dir = directory.joinpath(".git")
        if git_dir.exists() and git_dir.is_dir():
            return directory

    if expected_root_names:
        ern: Union[str, Path, List[Union[str, Path]]] = expected_root_names
        if isinstance(ern, (str, Path)):
            ern = [Path(ern).name]

        else:
            ern = [Path(p).name for p in ern]

        if directory.name in ern:
            return directory

    return get_root_dir(directory.parent, **kwargs)


def get_dir(path: str | Path, **kwargs):
    kwargs.setdefault("force_create_dir", False)
    kwargs.setdefault("create_dir", False)

    force_create_dir = kwargs["force_create_dir"]
    create_dir = kwargs["create_dir"]

    if not create_dir and force_create_dir:
        create_dir = True

    if not path:
        return ValueError("Path cannot be empty: %r" % path)

    if not isinstance(path, Path):
        path = Path(path)

    if not path.exists() and create_dir:
        path.mkdir(exist_ok=force_create_dir)

    if not path.is_dir():
        raise ValueError("Path is not a valid Directory: %r" % path)

    if path.exists() and path.is_dir():
        return path

    raise ValueError("Path doesn't exist or is invalid: %r" % path)
