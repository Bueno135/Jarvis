# Contributing to Jarvis

Thank you for your interest in contributing to Jarvis! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/jarvis.git
   cd jarvis
   ```
3. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the verification script**
   ```bash
   python scripts/verify_system.py
   ```

## 📋 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation if needed
- Ensure all tests pass

### 3. Run Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=core tests/

# Run specific test file
python -m pytest tests/test_integration_real.py
```

### 4. Verify Your Changes

```bash
# Run system verification
python scripts/verify_system.py

# Test basic functionality
python examples/basic_usage.py
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with a clear description of your changes.

## 📝 Code Style

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use 4 spaces for indentation
- Maximum line length: 88 characters
- Use f-strings for string formatting

### Documentation

- Add docstrings to all public functions and classes
- Use the following format:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of the function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: Description of when this exception is raised
    """
    pass
```

### Type Hints

- Use type hints for all function signatures
- Import types from the `typing` module when needed

```python
from typing import Dict, List, Optional, Any

def process_data(data: Dict[str, Any]) -> List[str]:
    """Process input data and return results."""
    pass
```

## 🧪 Testing

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern

```python
def test_plugin_execution_success(mock_kernel, mock_command_context):
    """Test that plugin executes successfully."""
    # Arrange
    plugin = MyPlugin()
    
    # Act
    result = plugin.execute(mock_command_context)
    
    # Assert
    assert result.success is True
    assert "expected message" in result.message
```

### Test Categories

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_unit_example():
    pass

@pytest.mark.integration
def test_integration_example():
    pass
```

## 🔌 Plugin Development

### Creating a New Plugin

1. **Create plugin file** in `plugins/category/`
2. **Inherit from BasePlugin**:

```python
from plugins.base_plugin import BasePlugin
from core.interfaces import CommandContext, CommandResult

class MyPlugin(BasePlugin):
    def name(self) -> str:
        return "MyPlugin"
    
    def patterns(self) -> List[str]:
        return ["mycommand", "do something"]
    
    def _execute_impl(self, ctx: CommandContext) -> CommandResult:
        # Your implementation here
        return CommandResult(True, "Success!")
```

3. **Add tests** for your plugin
4. **Update documentation** if needed

### Plugin Guidelines

- Keep plugins focused on a single responsibility
- Validate input before processing
- Use proper error handling with custom exceptions
- Log important operations
- Return structured CommandResult objects

## 🐛 Bug Reports

### Reporting Bugs

1. **Check existing issues** first
2. **Use the bug report template**
3. **Provide detailed information**:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs

### Bug Report Template

```markdown
## Bug Description
Brief description of the bug

## Environment
- Python version:
- OS:
- Jarvis version:

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Logs
[Include relevant logs]

## Additional Context
[Any other relevant information]
```

## 💡 Feature Requests

### Proposing Features

1. **Check existing issues** and discussions
2. **Use the feature request template**
3. **Explain the use case** and benefits
4. **Consider implementation complexity**

### Feature Request Template

```markdown
## Feature Description
Clear description of the proposed feature

## Problem Statement
What problem does this solve?

## Proposed Solution
How you envision this feature working

## Alternatives Considered
Other approaches you've thought about

## Additional Context
[Any other relevant information]
```

## 📖 Documentation

### Types of Documentation

- **API Documentation**: Code-level documentation in docstrings
- **User Documentation**: README, guides, tutorials
- **Developer Documentation**: Architecture, contribution guide

### Updating Documentation

- Keep documentation in sync with code changes
- Use clear, concise language
- Include code examples
- Test all examples

## 🔍 Code Review

### Review Process

1. **Automated checks** must pass
2. **At least one human review** required
3. **Address all feedback** before merge
4. **Keep discussions constructive**

### Review Guidelines

- **Be constructive** and respectful
- **Focus on the code**, not the author
- **Explain reasoning** for suggestions
- **Ask questions** if something is unclear

## 🏷️ Commit Messages

### Format

Use the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(echo): add support for multiple languages
fix(security): validate input in shell commands
docs(readme): update installation instructions
test(kernel): add integration tests for plugin loading
```

## 🌟 Recognition

Contributors are recognized in:

- **README.md** contributors section
- **CHANGELOG.md** for significant contributions
- **Release notes** for new features and fixes

## 📞 Getting Help

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Check existing docs first

## 📜 License

By contributing to Jarvis, you agree that your contributions will be licensed under the same license as the project.

## 🙏 Thank You

Thank you for contributing to Jarvis! Your contributions help make this project better for everyone.
