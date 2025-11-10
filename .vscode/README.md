# VS Code Configuration

This directory contains VS Code workspace settings for the Blacklist Intelligence Platform.

## 📁 Files

### `settings.json`
Comprehensive workspace settings for Git, Python, Docker, Database, and editor behavior.

**Key Features**:
- **Git Automation**: Auto-fetch (3 min), auto-save (1 sec), post-commit push, smart commit
- **Python Development**: Flake8 linting, Black formatting, pytest integration, type checking
- **Editor Behavior**: Format on save, rulers at 100 chars, auto-import organization
- **Docker Integration**: Socket path configuration, container support
- **Database Tools**: PostgreSQL connection configuration for SQLTools
- **File Management**: Auto-exclude build artifacts, cache, and dependencies

### `tasks.json`
Comprehensive automated tasks for development workflow.

**Available Tasks** (Ctrl+Shift+P → "Tasks: Run Task"):

**Git Automation**:
- `Git: Auto Sync` - Pull + Push
- `Git: Commit and Push` - Stage + Commit + Push (with custom message)
- `Git: Pull Latest` - Pull only

**Docker Development**:
- `Docker: Start Dev Environment` - Launch all containers (default build task)
- `Docker: Stop All Services` - Stop all containers
- `Docker: Restart Services` - Restart all containers
- `Docker: View Logs` - View container logs
- `Docker: Rebuild All` - Rebuild all images from scratch

**Testing**:
- `Test: Run All Tests` - Full test suite with coverage (default test task)
- `Test: Run Unit Tests` - Unit tests only
- `Test: Run Integration Tests` - Integration tests only
- `Test: Run Security Tests` - Security tests (CSRF, rate limiting)

**Database**:
- `Database: Connect Shell` - PostgreSQL shell access
- `Database: Backup` - Create database backup

**Code Quality**:
- `Lint: Python (Flake8)` - Lint Python code
- `Format: Python (Black)` - Format Python code

**Health & Monitoring**:
- `Health: Check All Services` - Health check all containers

**Setup & Installation**:
- `Setup: Development Environment` - Complete dev environment setup (all-in-one)
- `Setup: Install Python Dependencies` - Install Python packages only
- `Setup: Install Frontend Dependencies` - Install Node.js packages only
- `Setup: Install VSCode Extensions` - Install recommended extensions

**Package & Deploy**:
- `Package: Single Image` - Package one Docker image for offline deployment
- `Package: All Images` - Package all images sequentially

### `launch.json`
Debug configurations for Flask, Pytest, and Docker.

**Available Configurations** (F5 to launch):
- `Python: Flask App` - Debug Flask application
- `Python: Current File` - Debug current Python file
- `Python: Pytest` - Debug tests
- `Docker: Attach to Flask` - Attach to running Flask container
- `Docker: Attach to Collector` - Attach to running Collector container

### `extensions.json`
Comprehensive recommended VS Code extensions (40+ extensions).

**Essential Extensions by Category**:

**Git Tools**:
- GitLens - Git supercharged
- Git Graph - Visualize git history
- Git History - View git log

**Python Development**:
- Python - Python language support
- Pylance - Fast, feature-rich language server
- Black Formatter - Code formatting
- Flake8 - Linting
- autoDocstring - Generate docstrings

**JavaScript/TypeScript/React**:
- ESLint - JavaScript linting
- Prettier - Code formatting
- Tailwind CSS - CSS utility classes
- Auto Close Tag / Auto Rename Tag

**Docker & Containers**:
- Docker - Container management
- Remote Containers - Dev containers
- Remote SSH - Remote development

**Database**:
- SQLTools - Database management
- SQLTools PostgreSQL Driver
- Redis Client - Redis management

**Code Quality**:
- Error Lens - Inline error display
- TODO Tree - Track TODOs
- Trailing Spaces - Highlight trailing spaces
- Code Spell Checker

**Testing**:
- Python Test Adapter - Visual test explorer
- Playwright - E2E testing

**API Testing**:
- REST Client - HTTP requests in VS Code
- Thunder Client - Lightweight API client

**Productivity**:
- TODO Highlight - Highlight TODOs
- Better Comments - Styled comments
- Bookmarks - Code navigation

### `snippets/python.json`
Code snippets for faster development.

**Available Snippets** (type prefix + Tab):
- `flaskroute` - Flask route template
- `flaskbp` - Flask blueprint template
- `pytest` - Pytest test function
- `dockerservice` - Docker Compose service
- `logger` - Logger setup
- `tryexcept` - Try-except with logging

## 🚀 Quick Start

### 1. Install Recommended Extensions
```
Ctrl+Shift+P → "Extensions: Show Recommended Extensions"
Click "Install All"
```

### 2. Enable Auto-Sync
Settings are pre-configured. Just start coding!

### 3. Debug Flask App
```
1. F5 → Select "Python: Flask App"
2. Set breakpoints
3. Navigate to http://localhost:2542
```

### 4. Run Tasks
```
Ctrl+Shift+P → "Tasks: Run Task" → Select task
```

### 5. Use Snippets
```
Type snippet prefix (e.g., "flaskroute") → Press Tab
```

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+G` | Open Source Control |
| `Ctrl+Enter` | Commit (in SCM input) |
| `F5` | Start Debugging |
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+` ` | Toggle Terminal |
| `Ctrl+Shift+B` | Run Build Task |

## 🔧 Customization

### Modify Settings
1. Open `.vscode/settings.json`
2. Add/modify settings
3. Save (auto-applies)

### Add Custom Tasks
1. Open `.vscode/tasks.json`
2. Add new task in `tasks` array
3. Run via Command Palette

### Create Custom Snippets
1. Create file in `.vscode/snippets/`
2. Follow snippet syntax
3. Use in files of matching language

## 📚 Documentation

- [VS Code Git](https://code.visualstudio.com/docs/sourcecontrol/overview)
- [VS Code Tasks](https://code.visualstudio.com/docs/editor/tasks)
- [VS Code Debugging](https://code.visualstudio.com/docs/editor/debugging)
- [VS Code Snippets](https://code.visualstudio.com/docs/editor/userdefinedsnippets)

## 🔗 Related Files

- `../.editorconfig` - Code style configuration
- `../.gitmessage` - Git commit template
- `../.gitignore` - Git ignore rules

---

**Version**: 1.0
**Last Updated**: 2025-11-10
**Maintainer**: jclee
