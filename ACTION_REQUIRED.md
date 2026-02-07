# ACTION REQUIRED: Fix TestPyPI Deployment

## Summary

The GitHub Actions workflow for publishing to TestPyPI is failing because **trusted publishers are not configured** on TestPyPI. This is a **configuration issue that must be fixed on the TestPyPI website**, not in the code.

## What is Trusted Publishing?

Trusted publishing is a secure method recommended by PyPI that uses GitHub's OIDC (OpenID Connect) to authenticate deployments without requiring API tokens. This is the modern, recommended approach.

## What You Need to Do

### Step 1: Configure TestPyPI Trusted Publisher

1. **Go to TestPyPI**: https://test.pypi.org/
2. **Log in** with your account that has permissions for the `pyptv` project
3. **Create the project first** if it doesn't exist:
   - You may need to do a manual upload first to create the project, OR
   - If the project already exists, skip to step 4
4. **Navigate to project settings**:
   - Go to https://test.pypi.org/manage/project/pyptv/settings/publishing/
5. **Add a new pending publisher** (if project doesn't exist yet) or **Add a new publisher** with these EXACT values:
   ```
   PyPI Project Name: pyptv
   Owner: alexlib
   Repository name: pyptv
   Workflow filename: publish-to-pypi.yml
   Environment name: testpypi
   ```
6. **Save** the configuration

### Step 2: Configure PyPI Trusted Publisher (for production releases)

Follow the same steps but on the production PyPI:

1. **Go to PyPI**: https://pypi.org/
2. **Log in** with your account
3. **Navigate to your pyptv project settings**:
   - Go to https://pypi.org/manage/project/pyptv/settings/publishing/
4. **Add a new publisher** with these EXACT values:
   ```
   PyPI Project Name: pyptv
   Owner: alexlib
   Repository name: pyptv
   Workflow filename: publish-to-pypi.yml
   Environment name: pypi
   ```
5. **Save** the configuration

### Step 3: Verify GitHub Environments

The GitHub repository should have two environments configured:
- `pypi`
- `testpypi`

To verify/create these:
1. Go to https://github.com/alexlib/pyptv/settings/environments
2. Check if both environments exist
3. If they don't exist, create them (no special configuration needed)

## Testing the Fix

Once you've configured the trusted publishers:

1. Go to https://github.com/alexlib/pyptv/actions/workflows/publish-to-pypi.yml
2. Click "Run workflow"
3. Select branch: `master`
4. Choose deploy target: `testpypi`
5. Click "Run workflow"

The workflow should now succeed!

## Why This Happened

The workflow was set up to use trusted publishing, but the corresponding configuration was never added on TestPyPI/PyPI. The workflow cannot function without this configuration because it's trying to use OIDC authentication, which requires both sides (GitHub and PyPI) to be configured.

## Important Notes

- **You cannot fix this issue by modifying code** - it requires configuration on PyPI/TestPyPI
- The configuration values MUST match exactly (case-sensitive)
- The workflow filename must be `publish-to-pypi.yml` (not the full path)
- The environment names must be exactly `testpypi` and `pypi` (lowercase)

## Need Help?

If you encounter issues:
1. See the detailed guide in `DEPLOYMENT.md`
2. Check PyPI's troubleshooting guide: https://docs.pypi.org/trusted-publishers/troubleshooting/
3. Verify the configuration values match exactly

## References

- [DEPLOYMENT.md](DEPLOYMENT.md) - Comprehensive deployment guide
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub OIDC with PyPI](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-pypi)
