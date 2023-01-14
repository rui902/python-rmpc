from pathlib import Path
from typing import List, Iterable


__all__ = [
    "get_dir",
    "get_root_dir",
]


def get_root_dir(path: str | Path = None, **kwargs):
    kwargs.setdefault("match_first_git_dir", False)
    kwargs.setdefault("expected_root_names", None)

    match_first_git_dir = kwargs["match_first_git_dir"]
    expected_root_names = kwargs["expected_root_names"]

    if path is None:
        path = Path(__file__)

    if not isinstance(path, Path):
        path = Path(path)

    if not path.exists():
        raise ValueError("Invalid Path: %r" % path)

    directory = path if path.is_dir() else path.parent

    if match_first_git_dir:
        git_dir = directory.joinpath(".git")
        if git_dir.exists() and git_dir.is_dir():
            return directory

    if expected_root_names:
        ern = expected_root_names
        expected_root_names = (
            [getattr(p, "name", p).lower() for p in ern]
        ) if isinstance(expected_root_names, (List, Iterable)) else [getattr(ern, "name", ern).lower()]

        if directory.name.lower() in expected_root_names:
            return directory

    return get_root_dir(directory, **kwargs)


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

    if not path.is_dir():
        raise ValueError("Path is not a valid Directory: %r" % path)

    if not path.exists() and create_dir:
        path.mkdir(exist_ok=force_create_dir)

    if path.exists() and path.is_dir():
        return path

    raise ValueError("Path doesn't exist or is invalid: %r" % path)
