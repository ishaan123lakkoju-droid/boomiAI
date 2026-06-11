# GitHub Setup and Commit Guide

## Prerequisites

This guide assumes you want to push the Boomi automation code to GitHub.

### Step 1: Install Git

1. Download Git from: https://git-scm.com/download/win
2. Run the installer and follow the default options
3. Verify installation by opening PowerShell and running:
   ```powershell
   git --version
   ```

### Step 2: Configure Git

Set up your Git identity:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Verify configuration:

```powershell
git config --global --list
```

---

## Committing to GitHub (Two Scenarios)

### Scenario A: Create a NEW repository on GitHub

1. Go to https://github.com/new
2. Create a new repository named `boomi-automation`
3. Choose visibility (Public or Private)
4. **Do NOT initialize with README, .gitignore, or license** (we'll do it locally)
5. Click "Create repository"
6. You'll see commands like:
   ```
   git remote add origin https://github.com/YOUR_USERNAME/boomi-automation.git
   git branch -M main
   git push -u origin main
   ```

### Scenario B: Use an EXISTING repository

Skip to the commit steps below.

---

## Commit Steps

Navigate to the project folder and execute these commands:

### 1. Initialize Git (first time only)

```powershell
cd C:\Users\pujal\OneDrive\Documents\boomiAI
git init
```

### 2. Add all files

```powershell
git add .
```

Verify files are staged:

```powershell
git status
```

### 3. Create initial commit

```powershell
git commit -m "Initial commit: Boomi automation framework with YAML manifest, Python client, and component creation"
```

### 4. Add remote origin (if new repository)

```powershell
git remote add origin https://github.com/YOUR_USERNAME/boomi-automation.git
```

### 5. Rename branch to main (optional, if needed)

```powershell
git branch -M main
```

### 6. Push to GitHub

```powershell
git push -u origin main
```

When prompted for authentication:
- **Method 1 (Recommended):** Use GitHub Personal Access Token (PAT)
  - Generate token at: https://github.com/settings/tokens/new
  - Scopes needed: `repo`, `workflow`
  - Use token as password

- **Method 2:** Use GitHub CLI
  - Install from: https://cli.github.com/
  - Run: `gh auth login`

---

## Files to Commit

The following files will be committed:

```
boomiAI/
├── boomi.py                                 # Main automation script
├── boomi manifest file.txt                  # YAML manifest
├── boomi_component_ids.csv                  # Component inventory (auto-generated)
├── BOOMI_AUTOMATION_DETAILED_GUIDE.md       # Complete documentation
├── BOOMI_AUTOMATION_DOCUMENTATION.md        # Additional documentation
├── AUTOMATION_RESULTS.md                    # Live execution results
├── README.md                                # Project overview
├── requirements.txt                         # Python dependencies
├── .env                                     # Environment variables (DO NOT COMMIT)
├── mq connector .xml                        # MQ configuration example
└── GITHUB_SETUP.md                          # This file
```

### Files to exclude (.gitignore)

Create or update `.gitignore`:

```
.env
.venv/
.vscode/
*.pyc
__pycache__/
*.log
.DS_Store
```

---

## After First Push

### For subsequent commits

```powershell
git add .
git commit -m "Your descriptive commit message"
git push
```

### Common commit messages

- `"Add subprocess XML fixes"`
- `"Update component IDs from live run"`
- `"Enhance CSV reuse functionality"`
- `"Fix manifest validation"`

---

## Troubleshooting

### "fatal: not a git repository"

Run from the project directory:

```powershell
git init
git remote add origin https://github.com/YOUR_USERNAME/boomi-automation.git
```

### "Permission denied (publickey)"

Use HTTPS instead of SSH:

```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/boomi-automation.git
```

### "Updates were rejected"

Your local branch is behind the remote:

```powershell
git pull origin main
git push origin main
```

---

## Recommended .gitignore

```
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Generated files
*.log
*.csv
*.pyc

# OS
.DS_Store
Thumbs.db
```

---

## Quick Reference

| Command | Purpose |
|---|---|
| `git init` | Initialize local Git repository |
| `git add .` | Stage all changes |
| `git commit -m "msg"` | Create a commit with message |
| `git remote add origin <url>` | Connect to GitHub repository |
| `git push -u origin main` | Push to GitHub (first time) |
| `git push` | Push subsequent commits |
| `git status` | Check current status |
| `git log` | View commit history |

---

## Next Steps

1. Install Git: https://git-scm.com/download/win
2. Configure Git with your name and email
3. Create a GitHub repository
4. Follow the "Commit Steps" section above
5. Verify on GitHub that files are pushed

For help, contact GitHub Support or visit: https://docs.github.com/
