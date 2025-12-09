# GitHub Branch Protection Setup Guide

This guide explains how to configure branch protection rules for the `local-llm-research-agent` repository to require Pull Requests for all external contributions.

## Setting Up Branch Protection Rules

### Step 1: Navigate to Branch Protection Settings

1. Go to your repository on GitHub
2. Click **Settings** (gear icon)
3. In the left sidebar, click **Branches** under "Code and automation"
4. Click **Add branch ruleset** (recommended) or **Add rule** under "Branch protection rules"

### Step 2: Configure Branch Ruleset (Recommended Method)

1. **Ruleset name**: `main-protection`

2. **Enforcement status**: `Active`

3. **Target branches**:
   - Click **Add target**
   - Select **Include default branch** or manually add `main`

4. **Branch rules** (enable these):

   - [x] **Restrict deletions** - Prevent branch deletion

   - [x] **Require a pull request before merging**
     - Required approvals: `1` (or more for larger teams)
     - [x] Dismiss stale pull request approvals when new commits are pushed
     - [x] Require review from code owners (if you have CODEOWNERS file)
     - [x] Require approval of the most recent reviewable push

   - [x] **Require status checks to pass**
     - [x] Require branches to be up to date before merging
     - Add status checks (if you have CI):
       - `test` (pytest)
       - `lint` (ruff)

   - [x] **Block force pushes** - Prevent force pushes to main

   - [ ] **Require signed commits** (optional, for high-security projects)

5. **Bypass list** (for maintainers only):
   - Add repository admins or specific maintainer teams who can bypass in emergencies

6. Click **Create** to save the ruleset

### Step 3: Alternative - Classic Branch Protection Rules

If you prefer classic branch protection:

1. Click **Add rule** under "Branch protection rules"
2. **Branch name pattern**: `main`
3. Enable:
   - [x] Require a pull request before merging
     - [x] Require approvals: 1
     - [x] Dismiss stale approvals
   - [x] Require status checks to pass before merging
   - [x] Require branches to be up to date before merging
   - [x] Do not allow bypassing the above settings
   - [x] Restrict who can push to matching branches (add yourself/team)

## Additional Repository Settings

### Settings > General > Pull Requests

Configure these for better PR workflow:

- [x] Allow merge commits
- [x] Allow squash merging (recommended for clean history)
- [ ] Allow rebase merging (optional)
- [x] Always suggest updating pull request branches
- [x] Automatically delete head branches (after merge)

### Settings > Actions > General

If using GitHub Actions:

- Fork pull request workflows: **Require approval for first-time contributors**

## CODEOWNERS File (Optional)

Create `.github/CODEOWNERS` to automatically request reviews:

```
# Default owners for everything
* @your-username

# Specific paths
/src/agent/ @your-username
/docker/ @your-username
```

## Verifying Protection is Active

After setup, verify:

1. Try pushing directly to `main` (should fail)
2. Create a test branch and PR
3. Verify PR requires approval before merge
4. Check that status checks run (if CI configured)

## For Team Projects

If you have a team:

1. Create a GitHub Team for maintainers
2. Add team to bypass list (for emergencies only)
3. Require reviews from team members
4. Consider requiring 2 approvals for critical paths
