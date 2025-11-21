# Contributing to GeoPlan Benchmark

Thank you for your interest in contributing to GeoPlan Benchmark! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion for improvement, please open an issue on GitHub with:
- A clear description of the problem or suggestion
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)

### Submitting Pull Requests

1. **Fork the repository** and create a new branch from `main`
2. **Make your changes** following the project's coding style
3. **Test your changes** to ensure they work correctly
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description of your changes

### Code Style

- Follow PEP 8 Python style guide
- Use type hints where appropriate
- Write clear docstrings for functions and classes
- Keep code concise and readable

### Adding New Features

- **New Agent Architectures**: Implement the `BaseAgent` interface in `geoplan_bench/agents/`
- **New Evaluation Metrics**: Add metric classes in `geoplan_bench/evaluation/metrics/`
- **New Tools**: Extend the toolset in `geoplan_bench/tools/`
- **Documentation**: Update relevant documentation files

### Testing

- Ensure existing functionality continues to work
- Add tests for new features when possible
- Test with different Python versions (3.8+)

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/earth-insights/geoplan-bench.git
cd geoplan-bench
```

2. Create and activate a virtual environment (venv or conda):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

4. Set up environment variables (see `env.example`)

## Questions?

If you have questions about contributing, please open an issue or contact the maintainers.

Thank you for contributing to GeoPlan Benchmark!

