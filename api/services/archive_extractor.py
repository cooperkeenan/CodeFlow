import io
import tarfile
from pathlib import Path


class UnsafeArchiveError(Exception):
    pass


class ArchiveExtractor:
    def extract(self, data: bytes, dest: Path) -> None:
        root = dest.resolve()
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tar:
            for member in tar.getmembers():
                if not (member.isfile() or member.isdir()):
                    continue
                target = (root / member.name).resolve()
                if target != root and root not in target.parents:
                    raise UnsafeArchiveError(f"Unsafe archive entry: {member.name}")
                tar.extract(member, root)
