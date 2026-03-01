# Deployment Guide for PyPTV

This guide explains how to publish PyPTV to PyPI and TestPyPI using GitHub Actions with trusted publishing.

## Trusted Publishing Setup

PyPTV uses GitHub's OIDC (OpenID Connect) trusted publishing feature to securely publish packages to PyPI without using long-lived API tokens. This is the recommended approach by PyPI.

### Prerequisites

1. Repository owner access to `alexlib/pyptv`
2. PyPI/TestPyPI account with permissions to add trusted publishers
3. GitHub Actions enabled in the repository

### Setting Up Trusted Publishers

#### For TestPyPI

1. Log in to [TestPyPI](https://test.pypi.org/)
2. Navigate to your project or create it first by doing a manual upload
3. Go to "Publishing" section in your project settings
4. Click "Add a new publisher"
5. Fill in the following details:
   - **PyPI Project Name**: `pyptv`
   - **Owner**: `alexlib`
   - **Repository name**: `pyptv`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: `testpypi`
6. Save the configuration

#### For PyPI (Production)

1. Log in to [PyPI](https://pypi.org/)
2. Navigate to your project `pyptv`
3. Go to "Publishing" section in your project settings
4. Click "Add a new publisher"
5. Fill in the following details:
   - **PyPI Project Name**: `pyptv`
   - **Owner**: `alexlib`
   - **Repository name**: `pyptv`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: `pypi`
6. Save the configuration

### GitHub Environments

The workflow uses GitHub Environments for additional security. Ensure the following environments exist in the repository:

1. **pypi** environment
   - Used for production releases
   - Can optionally require manual approval
   
2. **testpypi** environment
   - Used for test releases
   - Can optionally require manual approval

To create/verify environments:
1. Go to repository Settings → Environments
2. Create `pypi` and `testpypi` environments if they don't exist
3. Optionally configure protection rules (e.g., required reviewers)

## Publishing Process

### Publishing to TestPyPI (Manual)

1. Go to Actions tab in the GitHub repository
2. Select "Publish Python Package to PyPI" workflow
3. Click "Run workflow"
4. Select branch: `master`
5. Choose deploy target: `testpypi`
6. Click "Run workflow"

The workflow will:
- Build the package
- Publish to TestPyPI using trusted publishing
- Create a deployment record

### Publishing to PyPI (Release)

There are two ways to publish to PyPI:

#### Method 1: Create a GitHub Release (Recommended)
1. Create and push a version tag:
   ```bash
   git tag v0.x.x
   git push origin v0.x.x
   ```
2. Go to GitHub → Releases → "Draft a new release"
3. Select the tag you just created
4. Fill in release notes
5. Click "Publish release"

The workflow will automatically trigger and publish to PyPI.

#### Method 2: Manual Workflow Dispatch
1. Go to Actions tab in the GitHub repository
2. Select "Publish Python Package to PyPI" workflow
3. Click "Run workflow"
4. Select branch: `master`
5. Choose deploy target: `pypi`
6. Click "Run workflow"

## Troubleshooting

### "invalid-publisher" Error

If you see an error like:
```
Token request failed: the server refused the request for the following reasons:
* `invalid-publisher`: valid token, but no corresponding publisher
```

This means the trusted publisher configuration on PyPI/TestPyPI doesn't match the workflow. Verify:

1. The workflow file path is exactly: `.github/workflows/publish-to-pypi.yml`
2. The environment name matches: `testpypi` or `pypi`
3. The repository owner and name are correct: `alexlib/pyptv`
4. The trusted publisher was added on the correct PyPI instance (TestPyPI vs PyPI)

### Environment Not Found

If the workflow fails with environment errors:
1. Create the missing environment in Settings → Environments
2. Ensure the environment name matches what's in the workflow

### Build Failures

If the build step fails:
1. Check Python version compatibility
2. Verify `pyproject.toml` configuration
3. Test build locally:
   ```bash
   pip install build
   python -m build
   ```

## Workflow Configuration

The workflow file `.github/workflows/publish-to-pypi.yml` has three main jobs:

1. **build**: Builds the distribution packages (wheel and source distribution)
2. **publish-to-pypi**: Publishes to production PyPI (on release or manual trigger)
3. **publish-to-testpypi**: Publishes to TestPyPI (on manual trigger only)

### Important Notes

- The workflow uses `pypa/gh-action-pypi-publish@release/v1` action
- No API tokens are needed - authentication is handled via OIDC
- The `id-token: write` permission is required for trusted publishing
- Artifacts are shared between jobs for efficiency

## Testing Before Release

Always test on TestPyPI before publishing to PyPI:

1. Publish to TestPyPI using manual workflow dispatch
2. Install from TestPyPI and test:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyptv
   ```
3. Verify the package works as expected
4. Then proceed with PyPI release

## Security Best Practices

1. Never commit API tokens to the repository
2. Use environment protection rules to require approvals for production deployments
3. Regularly review and rotate any API tokens (if used for other purposes)
4. Monitor the workflow runs for any suspicious activity
5. Keep the `pypa/gh-action-pypi-publish` action updated

## References

- [PyPI Help - Publishing](https://pypi.org/help/#publishing) - Official PyPI publishing documentation
- [GitHub OIDC with PyPI](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-pypi) - GitHub's guide for trusted publishing
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish) - The GitHub Action used for publishing
- [Trusted Publishers on PyPI](https://blog.pypi.org/posts/2023-04-20-introducing-trusted-publishers/) - Introduction to trusted publishers
