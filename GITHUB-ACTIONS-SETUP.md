# GitHub Actions Setup for PingDaddyPro v1.0.3

This document explains how to set up GitHub Actions for automatic Docker Hub deployment.

## Prerequisites

1. **Docker Hub Account:** Create account at [hub.docker.com](https://hub.docker.com)
2. **Docker Hub Repository:** Create repository `svejedobro/pingdaddypro`
3. **GitHub Repository:** Push code to [https://github.com/zaja/pingdaddypro](https://github.com/zaja/pingdaddypro)

## Setup Steps

### 1. Create Docker Hub Access Token

1. Go to [Docker Hub](https://hub.docker.com)
2. Click on your profile → **Account Settings**
3. Go to **Security** tab
4. Click **New Access Token**
5. Name: `pingdaddypro-github-actions`
6. Permissions: **Read, Write, Delete**
7. Copy the generated token

### 2. Add Secrets to GitHub Repository

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `DOCKER_HUB_USERNAME` | `svejedobro` | Docker Hub username |
| `DOCKER_HUB_ACCESS_TOKEN` | `your_token_here` | Docker Hub access token |

### 3. Workflow Features

The GitHub Actions workflow (`/.github/workflows/docker-build.yml`) will:

- **Trigger on:**
  - Push to `main` or `master` branch
  - Push tags starting with `v` (e.g., `v1.0.0`)
  - Pull requests to `main` or `master`

- **Build Images:**
  - Production image: `svejedobro/pingdaddypro:latest`
  - Development image: `svejedobro/pingdaddypro:dev`
  - Tagged versions: `svejedobro/pingdaddypro:v1.0.0`

- **Features:**
  - Multi-platform builds
  - Docker layer caching
  - Automatic tagging
  - Security scanning

## Usage

### Automatic Deployment

1. **Push to main branch:** Builds and pushes `latest` tag
2. **Create release tag:** 
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   This will build and push `v1.0.0` tag

### Manual Deployment

You can also manually trigger the workflow:

1. Go to **Actions** tab in GitHub
2. Select **Build and Push to Docker Hub**
3. Click **Run workflow**

## Docker Hub Images

After successful build, you'll find these images on Docker Hub:

- `svejedobro/pingdaddypro:latest` - Production image
- `svejedobro/pingdaddypro:dev` - Development image
- `svejedobro/pingdaddypro:v1.0.0` - Versioned image

## Pulling Images

```bash
# Production
docker pull svejedobro/pingdaddypro:latest

# Development
docker pull svejedobro/pingdaddypro:dev

# Specific version
docker pull svejedobro/pingdaddypro:v1.0.0
```

## Troubleshooting

### Common Issues

1. **Authentication Failed:**
   - Check Docker Hub username and token
   - Ensure token has correct permissions

2. **Build Failed:**
   - Check Dockerfile syntax
   - Verify all required files are present

3. **Push Failed:**
   - Check Docker Hub repository exists
   - Verify repository permissions

### Checking Workflow Status

1. Go to **Actions** tab in GitHub
2. Click on the workflow run
3. Check logs for detailed error messages

## Security Notes

- Access tokens are stored as encrypted secrets
- Tokens should have minimal required permissions
- Regularly rotate access tokens
- Monitor Docker Hub for unauthorized access

## Resources

- **GitHub Repository:** [https://github.com/zaja/pingdaddypro](https://github.com/zaja/pingdaddypro)
- **Docker Hub:** [https://hub.docker.com/r/svejedobro/pingdaddypro](https://hub.docker.com/r/svejedobro/pingdaddypro)
- **GitHub Actions Documentation:** [https://docs.github.com/en/actions](https://docs.github.com/en/actions)
- **Docker Hub Documentation:** [https://docs.docker.com/docker-hub/](https://docs.docker.com/docker-hub/)

