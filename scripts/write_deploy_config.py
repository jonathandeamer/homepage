#!/usr/bin/env python3
"""Write Hugo deploy config from explicit local environment variables."""

from __future__ import annotations

import os
import sys
from pathlib import Path


OUTPUT = Path(".hugo-deploy.generated.toml")
S3_ENV = "HOMEPAGE_S3_URL"
CF_ENV = "HOMEPAGE_CLOUDFRONT_DISTRIBUTION_ID"


def deploy_config(s3_url: str, distribution_id: str) -> str:
    return f'''[deployment]
  [[deployment.matchers]]
    pattern = '^sitemap\\.xml$'
    contentType = 'application/xml'
    cacheControl = 'public, max-age=0, must-revalidate'
  [[deployment.matchers]]
    pattern = '^.+\\.html$'
    cacheControl = 'public, max-age=0, must-revalidate'
  [[deployment.matchers]]
    pattern = '^.+\\.(?:jpg|jpeg|png|gif|webp|svg)$'
    cacheControl = 'max-age=31536000, no-transform, public'
  [[deployment.matchers]]
    pattern = '^.+\\.(?:woff2|woff)$'
    cacheControl = 'max-age=31536000, no-transform, public'

  [[deployment.targets]]
    name = "production"
    URL = "{s3_url}"
    cloudFrontDistributionID = "{distribution_id}"
'''


def main(argv: list[str]) -> int:
    output = Path(argv[0]) if argv else OUTPUT
    s3_url = os.environ.get(S3_ENV, "").strip()
    distribution_id = os.environ.get(CF_ENV, "").strip()

    missing = [name for name, value in ((S3_ENV, s3_url), (CF_ENV, distribution_id)) if not value]
    if missing:
        print(f"missing required environment variable(s): {', '.join(missing)}", file=sys.stderr)
        return 2
    if not s3_url.startswith("s3://"):
        print(f"{S3_ENV} must start with s3://", file=sys.stderr)
        return 2

    output.write_text(deploy_config(s3_url, distribution_id))
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
