# VS Code Configuration

This directory contains VS Code workspace settings for the Blacklist Intelligence Platform.

## 📁 Files

### `settings.json`
Workspace-specific settings for Git, Python, Docker, and general editor behavior.

**Key Features**:
- Auto-fetch: Every 3 minutes
- Auto-save: After 1 second delay
- Post-commit push: Enabled
- Smart commit: Stage + Commit in one action

### `tasks.json`
Automated tasks for Git operations.

**Available Tasks** (Ctrl+Shift+P → "Tasks: Run Task"):
- `Git: Auto Sync` - Pull + Push
- `Git: Commit and Push` - Stage + Commit + Push
- `Git: Pull Latest` - Pull only

### `launch.json`
Debug configurations for Flask, Pytest, and Docker.

**Available Configurations** (F5 to launch):
- `Python: Flask App` - Debug Flask application
- `Python: Current File` - Debug current Python file
- `Python: Pytest` - Debug tests
- `Docker: Attach to Flask` - Attach to running Flask container
- `Docker: Attach to Collector` - Attach to running Collector container

### `extensions.json`
Recommended VS Code extensions.

**Essential Extensions**:
- GitLens - Git supercharged
- Git Graph - Visualize git history
- Python - Python language support
- Docker - Docker container management
- Remote SSH - Remote development

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
