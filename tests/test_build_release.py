import importlib.util
import json
import unittest
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
