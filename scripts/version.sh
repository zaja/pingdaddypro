#!/bin/bash
# PingDaddyPro Version Management Script
# Usage: ./scripts/version.sh [patch|minor|major]

set -e

# Get current version
CURRENT_VERSION=$(grep 'APP_VERSION = ' pingdaddypro.py | cut -d'"' -f2)
echo "Current version: $CURRENT_VERSION"

# Parse version parts
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Determine version bump type
BUMP_TYPE=${1:-patch}

case $BUMP_TYPE in
    patch)
        PATCH=$((PATCH + 1))
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    *)
        echo "Usage: $0 [patch|minor|major]"
        exit 1
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "New version: $NEW_VERSION"

# Update version in pingdaddypro.py
sed -i "s/APP_VERSION = \"$CURRENT_VERSION\"/APP_VERSION = \"$NEW_VERSION\"/" pingdaddypro.py

# Update build date
BUILD_DATE=$(date +"%Y-%m-%d")
sed -i "s/BUILD_DATE = \"[^\"]*\"/BUILD_DATE = \"$BUILD_DATE\"/" pingdaddypro.py

# Get current commit hash
GIT_COMMIT=$(git rev-parse --short HEAD)
sed -i "s/GIT_COMMIT = \"[^\"]*\"/GIT_COMMIT = \"$GIT_COMMIT\"/" pingdaddypro.py

echo "Updated version to $NEW_VERSION"
echo "Build date: $BUILD_DATE"
echo "Git commit: $GIT_COMMIT"

# Commit changes
git add pingdaddypro.py
git commit -m "Bump version to $NEW_VERSION"

# Create and push tag
git tag "v$NEW_VERSION"
git push origin main
git push origin "v$NEW_VERSION"

echo "Version $NEW_VERSION has been released!"
echo "GitHub Release will be created automatically via GitHub Actions."
