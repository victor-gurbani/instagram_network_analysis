import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "03 analysis"))

import helper_functions


class ConfigLoadingTests(unittest.TestCase):
    def write_config(self, directory, filename, contents):
        config_path = Path(directory, filename)
        config_path.write_text(json.dumps(contents), encoding="utf-8")
        return config_path

    def test_default_path_is_repository_root_regardless_of_cwd(self):
        with mock.patch.dict(
            os.environ, {helper_functions.CONFIG_ENV_VAR: ""}, clear=False
        ):
            with mock.patch.object(
                helper_functions.os, "getcwd", return_value="/unrelated/directory"
            ):
                resolved_path = helper_functions.resolve_config_file_path()

        self.assertEqual(resolved_path, str(REPOSITORY_ROOT / "config.json"))
        self.assertTrue(os.path.isabs(resolved_path))

    def test_environment_override_supports_paths_relative_to_cwd(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            expected_path = self.write_config(
                temporary_directory, "alternate.json", {"username": "from-env"}
            )
            with mock.patch.dict(
                os.environ,
                {helper_functions.CONFIG_ENV_VAR: expected_path.name},
                clear=False,
            ):
                with mock.patch.object(
                    helper_functions.os,
                    "getcwd",
                    return_value=temporary_directory,
                ):
                    config = helper_functions.load_config()

        self.assertEqual(config, {"username": "from-env"})

    def test_explicit_path_takes_precedence_over_environment(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            explicit_path = self.write_config(
                temporary_directory, "explicit.json", {"username": "explicit"}
            )
            environment_path = self.write_config(
                temporary_directory, "environment.json", {"username": "environment"}
            )
            with mock.patch.dict(
                os.environ,
                {helper_functions.CONFIG_ENV_VAR: str(environment_path)},
                clear=False,
            ):
                config = helper_functions.load_config(explicit_path)

        self.assertEqual(config, {"username": "explicit"})

    def test_invalid_environment_override_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory, "missing.json")
            with mock.patch.dict(
                os.environ,
                {helper_functions.CONFIG_ENV_VAR: str(missing_path)},
                clear=False,
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    config = helper_functions.load_config()

        self.assertIsNone(config)

    def test_load_config_rejects_missing_malformed_and_non_object_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            cases = {
                "missing.json": None,
                "malformed.json": "{",
                "array.json": [],
            }
            for filename, contents in cases.items():
                config_path = Path(temporary_directory, filename)
                if contents is not None:
                    if isinstance(contents, str):
                        config_path.write_text(contents, encoding="utf-8")
                    else:
                        config_path.write_text(json.dumps(contents), encoding="utf-8")

                with self.subTest(filename=filename):
                    with contextlib.redirect_stdout(io.StringIO()) as output:
                        config = helper_functions.load_config(config_path)

                    self.assertIsNone(config)
                    self.assertIn(str(config_path), output.getvalue())

    def test_resolve_username_prefers_argument_and_normalizes_fallback(self):
        with mock.patch.object(helper_functions, "load_config") as load_config:
            self.assertEqual(
                helper_functions.resolve_username("  command-line-user  "),
                "command-line-user",
            )
            load_config.assert_not_called()

        self.assertEqual(
            helper_functions.resolve_username(
                None, {"username": "  configured-user  "}
            ),
            "configured-user",
        )

    def test_invalid_usernames_fail_cleanly(self):
        invalid_values = ("", "   ", None, 123)
        for invalid_value in invalid_values:
            with self.subTest(username=invalid_value):
                with contextlib.redirect_stdout(io.StringIO()):
                    username = helper_functions.get_username_from_config(
                        {"username": invalid_value}
                    )
                self.assertIsNone(username)


if __name__ == "__main__":
    unittest.main()
