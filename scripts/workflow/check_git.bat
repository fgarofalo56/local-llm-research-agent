@echo off
cd /d E:\Repos\GitHub\MyDemoRepos\local-llm-research-agent
echo === Git Status ===
git status --short
echo.
echo === Staged Changes ===
git diff --cached --stat
echo.
echo === Unstaged Changes ===
git diff --stat
