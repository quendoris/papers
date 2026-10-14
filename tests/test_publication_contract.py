"""Unit tests of SHA-256 and manifest validation (no signing key required)."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_papers import InvalidRelease, verify_release


def build_fixture(root: Path):
    folder = root / "publications" / "puzzles" / "constructive-million" / "v1.0.0"
    folder.mkdir(parents=True)
    pdf = b"%PDF-1.4\n% local synthetic verification fixture\n"
    (folder / "article.pdf").write_bytes(pdf)
    sha = hashlib.sha256(pdf).hexdigest()
    data = {
        "schema": "quendoris-papers-v1",
        "paper_id": "constructive-million",
        "version": "v1.0.0",
        "title": "A test only",
        "published_utc": "2026-10-14T20:00:00Z",
        "source": {
            "repository": "https://github.com/quendoris/implicit-sliding-puzzles",
            "commit": "0123456789abcdef0123456789abcdef01234567"
        },
        "files": [{"path": "article.pdf", "sha256": sha}]
    }
    (folder / "manifest.json").write_text(json.dumps(data, sort_keys=True) + "\n")
    (folder / "SHA256SUMS").write_text(f"{sha}  article.pdf\n")
    (folder / "manifest.json.minisig").write_text("unused-local-fixture\n")
    return folder, data


class VerifyPapersTests(unittest.TestCase):
    def test_matching_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, _ = build_fixture(Path(tmp))
            out = verify_release(folder, require_signature=False)
            self.assertEqual(out["status"], "ok")
            self.assertEqual(out["files_verified"], 1)

    def test_tampered_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, _ = build_fixture(Path(tmp))
            (folder / "article.pdf").write_bytes(b"tampered")
            with self.assertRaisesRegex(InvalidRelease, "SHA-256 mismatch"):
                verify_release(folder, require_signature=False)

    def test_mismatched_sums(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, _ = build_fixture(Path(tmp))
            (folder / "SHA256SUMS").write_text("")
            with self.assertRaisesRegex(InvalidRelease, "SHA256SUMS"):
                verify_release(folder, require_signature=False)

    def test_reject_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, data = build_fixture(Path(tmp))
            data["files"][0]["path"] = "some/../article.pdf"
            (folder / "manifest.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(InvalidRelease, "unsafe asset path"):
                verify_release(folder, require_signature=False)

    def test_release_requires_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, _ = build_fixture(Path(tmp))
            (folder / "manifest.json.minisig").unlink()
            with self.assertRaisesRegex(InvalidRelease, "missing signature"):
                verify_release(folder, require_signature=True)

    def test_extra_unlisted_files_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, _ = build_fixture(Path(tmp))
            (folder / "forgotten.txt").write_text("not listed")
            with self.assertRaisesRegex(InvalidRelease, "unexpected/missing"):
                verify_release(folder, require_signature=False)


if __name__ == "__main__":
    unittest.main()
