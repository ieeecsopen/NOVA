import hashlib
import json

import pytest

from compiler.nova_compiler.pkg import verify_lockfile


def write_lockfile(path, archive_name, digest):
    path.write_text(
        json.dumps({"lockfile_version": 1, "packages": {
            "demo": {"source": archive_name, "sha256": digest}
        }}),
        encoding="utf-8",
    )


def test_verify_lockfile_accepts_matching_digest(tmp_path):
    archive = tmp_path / "demo.tar.gz"
    archive.write_bytes(b"package contents")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    lockfile = tmp_path / "nova.lock"
    write_lockfile(lockfile, archive.name, digest)

    assert verify_lockfile(str(lockfile), str(tmp_path))


def test_verify_lockfile_rejects_modified_archive(tmp_path):
    archive = tmp_path / "demo.tar.gz"
    archive.write_bytes(b"package contents")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.write_bytes(b"tampered contents")
    lockfile = tmp_path / "nova.lock"
    write_lockfile(lockfile, archive.name, digest)

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_lockfile(str(lockfile), str(tmp_path))


def test_verify_lockfile_rejects_malformed_digest(tmp_path):
    archive = tmp_path / "demo.tar.gz"
    archive.write_bytes(b"package contents")
    lockfile = tmp_path / "nova.lock"
    write_lockfile(lockfile, archive.name, "not-a-digest")

    with pytest.raises(ValueError, match="invalid SHA-256"):
        verify_lockfile(str(lockfile), str(tmp_path))
