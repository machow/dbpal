import fsspec

from dataclasses import dataclass


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

