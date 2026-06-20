import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from scripts.write_deploy_config import deploy_config, main


class DeployConfigTests(TestCase):
    def test_deploy_config_contains_target_and_cache_matchers(self) -> None:
        text = deploy_config("s3://jonathandeamer.com?region=eu-west-2", "E123")

        self.assertIn('name = "production"', text)
        self.assertIn('URL = "s3://jonathandeamer.com?region=eu-west-2"', text)
        self.assertIn('cloudFrontDistributionID = "E123"', text)
        self.assertIn("must-revalidate", text)
        self.assertIn("max-age=31536000", text)

    def test_main_fails_when_required_env_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "deploy.toml"
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(main([str(output)]), 2)
            self.assertFalse(output.exists())

    def test_main_writes_config_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "deploy.toml"
            env = {
                "HOMEPAGE_S3_URL": "s3://jonathandeamer.com?region=eu-west-2",
                "HOMEPAGE_CLOUDFRONT_DISTRIBUTION_ID": "E123",
            }
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(main([str(output)]), 0)
            self.assertIn('URL = "s3://jonathandeamer.com?region=eu-west-2"', output.read_text())
