import contextlib
import fsspec
import os

from dataclasses import dataclass


@contextlib.contextmanager
def set_env(**kwargs):
    """
    Temporarily set the process environment variables.
    """
    old_environ = dict(os.environ)
    for k, v in kwargs.items():
        if k in os.environ:
            del os.environ[k]

        os.environ[k] = v

    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)



@dataclass
class TempBucket:
    fs: fsspec.AbstractFileSystem
    dirname: str

    def teardown(self):
        if self.dirname.startswith("/"):
            raise ValueError(f"dirname starts with a '/': {dirname}")

        self.fs.rm(self.dirname, recursive=True)

    @classmethod
    def from_protocol(cls, protocol, dirname):
        fs = fsspec.filesystem(protocol)
        fs.mkdir(dirname, create_parents=True)

        return cls(fs, dirname)

