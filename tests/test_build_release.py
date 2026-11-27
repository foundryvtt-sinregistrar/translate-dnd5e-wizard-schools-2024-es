import importlib.util
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "dev-tools" / "buildScripts" / "build_release.py"
SPEC = importlib.util.spec_from_file_location("build_release", SCRIPT)
BUILD_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_RELEASE)


class ReleaseConfigurationTests(unittest.TestCase):
    def test_profile_matches_manifest_identity(self):
        profile = json.loads((ROOT / "dev-tools" / "buildScripts" / "release-profile.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "module.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["archive_name"], manifest["id"])
        self.assertEqual(profile["manifest_channel"], "latest")

    def test_manifest_uses_versioned_release_download(self):
        manifest = json.loads((ROOT / "module.json").read_text(encoding="utf-8"))
        expected = f"{manifest['url']}/releases/download/v{manifest['version']}/{manifest['id']}.zip"
        self.assertEqual(manifest["download"], expected)

    def test_version_format_is_accepted(self):
        manifest = json.loads((ROOT / "module.json").read_text(encoding="utf-8"))
        self.assertIsNotNone(BUILD_RELEASE.SAFE_VERSION.fullmatch(manifest["version"]))

    def test_real_git_archive_excludes_documentation_and_passes_validation(self):
        raw_manifest = (ROOT / "module.json").read_bytes()
        manifest = json.loads(raw_manifest)
        prefix = manifest["id"] + "/"
        with tempfile.TemporaryDirectory(prefix="wizard-translation-archive-") as temporary:
            archive_path = Path(temporary) / "module.zip"
            subprocess.run([
                "git", "-c", f"safe.directory={ROOT.as_posix()}", "archive", "--worktree-attributes",
                "--format=zip", f"--prefix={prefix}", "-o", str(archive_path), "HEAD"
            ], cwd=ROOT, check=True, capture_output=True)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertFalse(any(name.startswith(prefix + "docs/") for name in archive.namelist()))
                self.assertFalse(any(name.startswith(prefix + "tests/") for name in archive.namelist()))
            BUILD_RELEASE.validate_archive(archive_path, raw_manifest, manifest)
