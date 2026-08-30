# Publishing

Releases are published to PyPI automatically when a matching version tag is pushed.

1. Update the version in `pyproject.toml` and commit the change.
2. Create and push a version tag:

   ```sh
   git tag v0.1.1
   git push origin main --tags
   ```

The workflow builds the package, generates attestations, and publishes it to PyPI using the configured `pypi` GitHub environment.
