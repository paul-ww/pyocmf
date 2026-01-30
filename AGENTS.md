# AGENTS.md

## Project Overview

pyocmf is a Python library for parsing and validating Open Charge Metering Format (OCMF) data. OCMF is a standardized format for metering data from electric vehicle charging stations, ensuring transparency and tamper-proof documentation of charging sessions.

The library provides:
- Parsing of OCMF strings and XML files
- Validation using Pydantic models
- Type-safe handling of identifiers, units, and cryptographic signatures
- Support for cable loss compensation and reading data

**Key Technologies:**
- Python 3.11+
- Pydantic for data validation
- uv for dependency management and builds
- pytest for testing
- ty for type checking
- ruff for linting and formatting

**Project Structure:**
- `src/pyocmf/`: Main package code
  - `ocmf.py`: Core OCMF model and parsing
  - `sections/`: Payload, signature, and reading models
  - `types/`: Type definitions (identifiers, units, crypto, cable loss)
  - `utils/`: XML parsing utilities
  - `exceptions.py`: Custom exception types
- `test/`: Test suite
  - `test_ocmf/`: Unit tests organized by module
  - `resources/`: Test data and fixtures

## Setup Commands

This project uses `uv` (a fast Python package installer and resolver) for dependency management.

**Install uv (if not already installed):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install dependencies:**
```bash
uv sync
```

**Install development dependencies:**
Development dependencies are automatically included with `uv sync` (includes ty, pytest, ruff).

**Activate virtual environment (optional):**
```bash
source .venv/bin/activate
```

Note: You can run commands directly with `uv run` without activating the virtual environment.

## Development Workflow

**Run Python scripts or modules:**
```bash
uv run python -m pyocmf
uv run python your_script.py
```

**Interactive Python shell with project installed:**
```bash
uv run python
```

**Add new dependencies:**
```bash
# Runtime dependency
uv add <package-name>

# Development dependency
uv add --dev <package-name>
```

**Update dependencies:**
```bash
uv sync --upgrade
```

## Testing Instructions

**Run all tests:**
```bash
uv run pytest
```

**Run tests with verbose output:**
```bash
uv run pytest -v
```

**Run specific test file:**
```bash
uv run pytest test/test_ocmf/test_roundtrip.py
```

**Run specific test by name:**
```bash
uv run pytest test/test_ocmf/test_types/test_identifiers.py::test_specific_function
```

**Run tests matching a pattern:**
```bash
uv run pytest -k "test_pattern"
```

**Test file organization:**
- Tests are located in `test/test_ocmf/`
- Test files follow the pattern `test_*.py`
- Test resources and fixtures are in `test/resources/`
- The project uses pytest with configuration in `pyproject.toml`

**Important testing notes:**
- Tests must pass before merging
- The project has submodules - clone with `git clone --recursive` or run `git submodule update --init --recursive`
- CI tests run against Python 3.11, 3.12, and 3.13

## Code Style Guidelines

**Linting and formatting:**
The project uses ruff for both linting and formatting.

**Run ruff linter:**
```bash
uv run ruff check .
```

**Run ruff linter with auto-fix:**
```bash
uv run ruff check --fix .
```

**Run ruff formatter:**
```bash
uv run ruff format .
```

**Check formatting without changes:**
```bash
uv run ruff format --check .
```

**Type checking:**
```bash
uv run ty check src test
```

Or using poe:
```bash
uv run poe typecheck
```

**Run all code quality checks (lint + format + type check):**
```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check src test
```

**Code style conventions:**
- Line length: 100 characters (configured in `ruff.toml`)
- McCabe complexity: Maximum of 12 (configured in `ruff.toml`)
- Type hints required: All function definitions must have complete type annotations
- Import organization: Imports are automatically sorted by ruff (isort rules)
- Preview mode enabled in ruff for access to experimental linting rules
- Enabled ruff rules include:
  - E/W: pycodestyle errors and warnings
  - F: Pyflakes
  - C901/C4: McCabe complexity and comprehension complexity
  - TRY: Exception handling best practices
  - N: PEP8 naming conventions
  - B: flake8-bugbear (common bugs)
  - UP: pyupgrade (modern Python syntax)
  - I: isort (import sorting)
  - PT: pytest style
  - PTH: pathlib usage
  - EXE: Executable shebang validation
  - ERA: eradicate (find dead code)
  - DTZ: datetime-tz (datetime best practices)
  - EM: error-message formatting
  - FA: future annotations
  - PIE: flake8-pie (misc performance and style)
  - FURB: refurb (modern Python idioms)
  - PGH: pygrep hooks
  - BLE: blind exception catching
  - D (selective): Docstring formatting and quality checks
    - Enforces proper formatting for existing docstrings (indentation, quotes, punctuation)
    - Validates section structure (Args, Returns, Raises)
    - Does NOT require docstrings on all functions (only validates when present)
  - See `ruff.toml` for complete configuration

**ty configuration:**
- Type checking using `ty check` command
- Checks both `src` and `test` directories
- All functions must have complete type hints
- Pydantic support included

**File organization:**
- Source code in `src/pyocmf/`
- Use `__init__.py` to expose public API
- Group related functionality in subdirectories (sections/, types/, utils/)
- Follow Python package naming conventions (lowercase, underscores)

## Build and Deployment

**Build the package:**
```bash
uv build
```

This creates distribution files in the `dist/` directory (wheel and source distribution).

**Install package locally in editable mode:**
```bash
uv pip install -e .
```

**Package version:**
Version is defined in `pyproject.toml` under `[project]` section.

**Build system:**
Uses `uv_build>=0.8.3` as the build backend (configured in `pyproject.toml`).

## CI/CD Pipeline

The project uses GitHub Actions with two workflows:

**Lint workflow (`.github/workflows/lint.yml`):**
- Triggers on push/PR to `initial-version` and `main` branches
- Runs ruff linting and formatting checks
- Runs ty type checking
- Uses Python version from `pyproject.toml`

**Test workflow (`.github/workflows/test.yml`):**
- Triggers on push/PR to `initial-version` and `main` branches
- Runs pytest across Python 3.11, 3.12, and 3.13
- Clones submodules recursively (required for test resources)

**Before committing:**
1. Run `uv run ruff check .` and fix any issues
2. Run `uv run ruff format .` to format code
3. Run `uv run ty check src test` and fix type errors
4. Run `uv run pytest` and ensure all tests pass

Or use poe commands for convenience:
```bash
uv run poe lint-fix    # Auto-fix linting issues
uv run poe format      # Format code
uv run poe typecheck   # Run type checking
uv run poe test        # Run tests
```

## Pull Request Guidelines

**Branch strategy:**
- Main development branch: `initial-version`
- Create feature branches from `initial-version`

**Before submitting a PR:**
1. Ensure all code quality checks pass:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run ty check src test
   uv run pytest
   ```
   
   Or use poe commands:
   ```bash
   uv run poe lint
   uv run poe format-check
   uv run poe typecheck
   uv run poe test
   ```

2. All tests must pass
3. No linting or formatting errors
4. No type errors

**PR requirements:**
- Code must pass all CI checks (lint and test workflows)
- Tests should be added for new features
- Type hints must be complete and accurate

## Common Commands Quick Reference

```bash
# Setup
uv sync                              # Install all dependencies

# Development
uv run python -m pyocmf              # Run module
uv run python                        # Interactive shell

# Testing
uv run pytest                        # Run all tests
uv run pytest -v                     # Verbose output
uv run pytest -k "pattern"           # Run tests matching pattern
uv run poe test                      # Run tests (with poe)

# Code Quality
uv run ruff check .                  # Lint code
uv run ruff check --fix .            # Lint and auto-fix
uv run ruff format .                 # Format code
uv run ty check src test             # Type check

# Code Quality (using poe)
uv run poe lint                      # Lint code
uv run poe lint-fix                  # Lint and auto-fix
uv run poe format                    # Format code
uv run poe format-check              # Check formatting without changes
uv run poe typecheck                 # Type check

# Build
uv build                             # Build package distributions
uv run poe docs                      # Build documentation
uv run poe demo                      # Run Pyodide demo locally

# Dependencies
uv add <package>                     # Add runtime dependency
uv add --dev <package>               # Add dev dependency
uv sync --upgrade                    # Update all dependencies
```

## Git Submodules

This repository contains git submodules for test resources.

**Clone with submodules:**
```bash
git clone --recursive <repository-url>
```

**Initialize submodules in existing clone:**
```bash
git submodule update --init --recursive
```

**Update submodules:**
```bash
git submodule update --remote
```

## Troubleshooting

**Common issues:**

1. **Tests fail with missing resources:**
   - Ensure submodules are initialized: `git submodule update --init --recursive`

2. **Import errors when running Python:**
   - Make sure dependencies are installed: `uv sync`
   - Verify you're using the correct Python version (3.11+)

3. **Type checking errors:**
   - ty checks both `src` and `test` directories
   - Ensure all functions have complete type annotations
   - Check Pydantic models use proper type hints

4. **Ruff formatting conflicts:**
   - Run `uv run ruff format .` to auto-format
   - The formatter is consistent with linting rules

5. **uv command not found:**
   - Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Ensure uv is in your PATH

## Additional Notes

**Python version compatibility:**
- Requires Python 3.11 or higher
- Tested on 3.11, 3.12, and 3.13

**Key dependencies:**
- `pydantic>=2.10.4`: Data validation and settings management
- `pydantic-extra-types>=2.10.1`: Additional Pydantic types
- `ciso8601>=2.3.2`: Fast ISO 8601 date/time parsing
- `phonenumbers>=9.0.10`: Phone number parsing and validation

**OCMF format:**
- OCMF strings follow the format: `OCMF|{payload_json}|{signature_json}`
- The library handles both string and XML representations
- See `spec/OCMF-Open-Charge-Metering-Format/` for format specification

**When adding new features:**
- Add corresponding tests in `test/test_ocmf/`
- Update type hints and ensure ty passes
- Follow existing code organization patterns
- Update exceptions in `exceptions.py` if adding new error types
- Export public APIs through `__init__.py`

## Task Automation with Poe

The project uses [Poe the Poet](https://poethepoet.natn.io/) for task automation. All poe tasks are defined in `pyproject.toml` under `[tool.poe.tasks]`.

**Available poe tasks:**

```bash
uv run poe test           # Run tests with pytest (stops on first failure)
uv run poe lint           # Run ruff linter
uv run poe lint-fix       # Run ruff linter with auto-fix
uv run poe format         # Format code with ruff
uv run poe format-check   # Check code formatting without changes
uv run poe typecheck      # Run ty type checker
uv run poe docs           # Build documentation with mkdocs
uv run poe demo           # Run Pyodide demo locally
```

**Why use poe tasks?**
- Shorter, more memorable commands
- Consistent interface across different tools
- Easy to extend with new tasks
- All tasks defined in one place (`pyproject.toml`)

## Code Commenting Guidelines

### Core Principle
**Write code that speaks for itself. Comment only when necessary to explain WHY, not WHAT.**
We do not need comments most of the time.

### ❌ AVOID These Comment Types

**Obvious Comments**
```python
# Bad: States the obvious
counter = 0  # Initialize counter to zero
counter += 1  # Increment counter by one
```

**Redundant Comments**
```python
# Bad: Comment repeats the code
def get_user_name():
    return user.name  # Return the user's name
```

**Outdated Comments**
```python
# Bad: Comment doesn't match the code
# Calculate tax at 5% rate
tax = price * 0.08  # Actually 8%
```

### ✅ WRITE These Comment Types

**Complex Business Logic**
```python
# Good: Explains WHY this specific calculation
# Apply progressive tax brackets: 10% up to 10k, 20% above
tax = calculate_progressive_tax(income, [0.10, 0.20], [10000])
```

**Non-obvious Algorithms**
```python
# Good: Explains the algorithm choice
# Using Floyd-Warshall for all-pairs shortest paths
# because we need distances between all nodes
for k in range(vertices):
    for i in range(vertices):
        for j in range(vertices):
            # ... implementation
```

**Regex Patterns**
```python
# Good: Explains what the regex matches
# Match email format: username@domain.extension
email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
```

**API Constraints or Gotchas**
```python
# Good: Explains external constraint
# GitHub API rate limit: 5000 requests/hour for authenticated users
await rate_limiter.wait()
response = await fetch(github_api_url)
```

**OCMF-specific Examples**
```python
# Good: Explains OCMF format constraint
# OCMF spec requires ISO 8601 format with timezone for all timestamps
timestamp = datetime.now(timezone.utc).isoformat()

# Good: Explains validation rule
# Signature algorithm must be one of the values defined in OCMF spec Table 22
if signature.algorithm not in ["ECDSA-secp192k1-SHA256", "ECDSA-secp256k1-SHA256"]:
    raise ValidationError(...)
```

### Decision Framework

Before writing a comment, ask:
1. **Is the code self-explanatory?** → No comment needed
2. **Would a better variable/function name eliminate the need?** → Refactor instead
3. **Does this explain WHY, not WHAT?** → Good comment
4. **Will this help future maintainers?** → Good comment

### When to Use Docstrings

**Docstrings ARE required for:**
- **Public APIs** - Any function, class, or method that external users will call
- **Complex business logic** - When the implementation involves non-obvious OCMF rules or calculations
- **Non-obvious behavior** - Edge cases, side effects, or important constraints that aren't apparent from type hints

**Docstrings are NOT needed for:**
- **Private/internal functions** - If the function name, parameters, and type hints clearly convey intent
- **Obvious operations** - Simple getters, setters, or straightforward data transformations
- **Self-explanatory code** - When good variable names and clear structure tell the story

**Public API Example (docstring required):**
```python
def parse_ocmf_from_xml(xml_path: Path) -> OCMF:
    """Parse an OCMF model from an XML file.

    This follows the Transparenzsoftware XML format specification.

    Args:
        xml_path: Path to the XML file containing OCMF data

    Returns:
        Parsed and validated OCMF model

    Raises:
        XmlParsingError: If the XML file cannot be parsed
        ValidationError: If the OCMF data fails validation
    """
    # ... implementation
```

**Internal Function Example (no docstring needed):**
```python
def _validate_pagination_sequence(current: int, previous: int) -> bool:
    """Not needed - function name and types are self-explanatory."""
    return current == previous + 1
```

Better as:
```python
def _validate_pagination_sequence(current: int, previous: int) -> bool:
    return current == previous + 1
```

**Complex Internal Logic Example (docstring helpful):**
```python
def _calculate_cable_loss_compensation(
    reading_value: float,
    cable_resistance: float,
    current: float,
) -> float:
    """Calculate energy loss in charging cable per OCMF spec Table 24.
    
    The compensation accounts for I²R losses in the charging cable between
    the meter and the vehicle. This is required for billing accuracy under
    German Eichrecht when cable resistance exceeds 10 mΩ.
    """
    # ... complex calculation
```

**Configuration and Constants**
```python
# Good: Explains the source or reasoning
MAX_RETRIES = 3  # Based on OCMF spec recommendation for signature verification
SIGNATURE_ENCODING = "utf-8"  # OCMF spec requires UTF-8 for all text fields
```

**Annotations**
```python
# TODO: Add support for OCMF v1.0 backward compatibility after spec review
# FIXME: Memory leak in XML parser - investigate defusedxml usage
# HACK: Workaround for pydantic v2.10.4 bug - remove after upgrade
# NOTE: This implementation assumes UTC timezone for all OCMF timestamps
# WARNING: This function modifies the signature object instead of creating a copy
# PERF: Consider caching parsed XML if loading same file repeatedly
# SECURITY: Validate signature before trusting any metering data
# BUG: Edge case failure when payload is empty - needs investigation
# REFACTOR: Extract XML parsing logic into separate utility for reusability
# DEPRECATED: Use parse_ocmf_from_xml() instead - this will be removed in v1.0
```

### Anti-Patterns to Avoid

**Dead Code Comments**
```python
# Bad: Don't comment out code (use git history instead)
# def old_parse_function(data: str) -> dict:
#     ...

def new_parse_function(data: str) -> OCMF:
    ...
```

**Changelog Comments**
```python
# Bad: Don't maintain history in comments (use git commits)
# Modified by John on 2023-01-15
# Fixed bug reported by Sarah on 2023-02-03
def process_ocmf_data():
    # ... implementation
```

**Divider Comments**
```python
# Bad: Don't use decorative comments
# =====================================
# UTILITY FUNCTIONS
# =====================================
```

### Quality Checklist

Before committing, ensure your code and comments:
- [ ] **Public APIs have docstrings** - All user-facing functions/classes are documented
- [ ] **Internal code is self-documenting** - Good names and clear structure eliminate need for comments
- [ ] **Comments explain WHY, not WHAT** - Code shows what it does, comments explain reasoning
- [ ] **Docstrings are concise but complete** - Include Args, Returns, Raises when relevant
- [ ] **No unnecessary docstrings** - Private functions with clear names don't need them
- [ ] Are grammatically correct and clear
- [ ] Will remain accurate as code evolves
- [ ] Are placed appropriately (above the code they describe)
- [ ] Use proper spelling and professional language
- [ ] Follow Python docstring conventions (Google/NumPy style)

### Summary

**Code should be self-documenting first.** Write clear, descriptive names and well-structured code that doesn't need explanation.

**Docstrings are for public APIs and complex business logic.** Users of your library need documentation. Internal implementation should speak for itself.

**Comments explain WHY, not WHAT.** If you need a comment, it should explain reasoning, constraints, or non-obvious decisions—not describe what the code does.

When in doubt: Good names + type hints + Pydantic models > comments > docstrings for internal code.
