# Form Automator

A robust and production-ready Python application designed to automate the process of filling and submitting web forms. Built with resilience, security, and maintainability in mind, it uses a configuration-driven approach to handle complex forms without changing a line of code.

## Key Features

-   **Configuration-Driven**: Define form-filling logic in simple YAML or JSON files. No coding required for new forms.
-   **Secure**: Handles sensitive data (like passwords) securely via environment variables, keeping secrets out of your configuration files.
-   **Resilient & Reliable**:
    -   Uses intelligent, explicit waits to handle dynamic page loads.
    -   Includes automatic retry logic with exponential backoff for transient network or element-loading issues.
    -   Eliminates flaky `time.sleep()` calls entirely.
-   **Structured Logging**: Produces machine-readable JSON logs (`structlog`) for easy integration with modern log analysis platforms.
-   **Screenshot on Failure**: Automatically captures screenshots at key stages (before, after, on-error) for easy debugging.
-   **Extensible Design**: The core logic is built using a Strategy Pattern, making it easy to add support for new types of form fields.
-   **CI/CD Ready**: Comes with a full-fledged GitHub Actions workflow for automated testing, linting, and type-checking across multiple Python versions.
-   **High Test Coverage**: Includes a comprehensive suite of unit and integration tests to ensure reliability.

## Prerequisites

-   Python 3.8+
-   Google Chrome (for the default Selenium WebDriver)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
    cd YOUR_REPOSITORY
    ```

2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The application is controlled by a configuration file (`.yaml` or `.json`) and an environment variable file (`.env`).

### 1. Environment Variables (`.env`)

Create a `.env` file in the root directory to store secrets. These variables can be referenced from your configuration file.

**Example `.env` file:**

```env
# .env
FORM_PASSWORD="your-secret-password-here"
FORM_EMAIL="test.user@example.com"
```

### 2. Configuration File (`production_form_config.yaml`)

Create a YAML file to define the form you want to fill. This file specifies the target URL, the fields to interact with, and post-submission success conditions.

**Example `production_form_config.yaml`:**

```yaml
# The URL of the web form
url: "https://example.com/login"

# --- Page Load Settings ---
page_load_timeout: 30 # Max seconds to wait for the page to be ready

# --- Form Fields ---
# A list of actions to perform on the page
fields:
  - selector: "user-email" # The HTML 'id' of the email input
    selector_type: "id"
    field_type: "input"
    value: "${FORM_EMAIL}" # Substitutes the value from .env file
    required: true

  - selector: "user-password"
    selector_type: "id"
    field_type: "input"
    value: "${FORM_PASSWORD}" # Substitutes a secret from .env file
    required: true

  - selector: "remember-me"
    selector_type: "id"
    field_type: "checkbox"
    value: true # Checks the box
    required: false # This field can fail without stopping the process

# --- Form Submission ---
submit_selector: "button[type='submit']"
submit_selector_type: "css"

# --- Success Condition ---
# After submission, wait for a specific condition to confirm success.
success_wait_condition:
  condition_type: "url_contains" # Wait until the page URL contains this string
  value: "/dashboard"
  timeout: 15 # Max seconds to wait for this condition

# --- Debugging ---
screenshot_dir: "./screenshots" # Directory to save screenshots
```

## Usage

Once your `.env` and configuration files are set up, run the application using the example entrypoint:

```bash
python usage_example.py
```

Logs will be printed to the console and saved to `form_filler.log` in JSON format. Screenshots (if configured) will be saved to the specified directory.

## For Developers

This project includes a complete suite of tools to ensure code quality and a smooth development experience.

### Setting Up the Development Environment

Install both application and development dependencies using the `Makefile`:

```bash
make install-dev
```

### Running Tests

The project has a full suite of unit and integration tests.

-   **Run all tests:**
    ```bash
    make test
    ```
-   **Run only fast unit tests:**
    ```bash
    make test-unit
    ```
-   **Run only integration tests (requires a browser driver):**
    ```bash
    make test-integration
    ```
-   **Run tests and generate a coverage report:**
    ```bash
    make test-coverage
    ```
    The HTML report will be available in the `htmlcov/` directory.

### Code Quality Checks

We use `black` for formatting, `flake8` for linting, and `mypy` for static type checking.

-   **Format all code:**
    ```bash
    make format
    ```
-   **Lint the codebase:**
    ```bash
    make lint
    ```
-   **Run static type checking:**
    ```bash
    make type-check
    ```
-   **Run all checks (lint, type-check, and tests):**
    ```bash
    make check-all
    ```

## Technology Stack

-   **Automation**: Selenium
-   **Logging**: Structlog
-   **Resilience**: Tenacity
-   **Configuration**: PyYAML, python-dotenv
-   **Testing**: Pytest, pytest-cov
-   **Code Quality**: Black, Flake8, Mypy

## Project Structure

```
.
├── .github/workflows/ci.yml   # GitHub Actions CI pipeline
├── your_project/              # Main application source code
│   ├── __init__.py
│   ├── config_manager.py      # Loads and validates configuration
│   ├── exceptions.py          # Custom application exceptions
│   ├── logger.py              # Structured logging setup
│   ├── models.py              # Data models (dataclasses) for config
│   └── selenium_form_filler.py  # Core Selenium automation logic
├── tests/                     # Automated tests
│   ├── unit/                  # Unit tests for isolated logic
│   └── integration/           # Integration tests using a live browser
├── .env.example               # Example environment file
├── Makefile                   # Developer command shortcuts
├── production_form_config.yaml # Example configuration
├── pytest.ini                 # Pytest configuration
├── requirements-dev.txt       # Development dependencies
├── requirements.txt           # Application dependencies
└── usage_example.py           # Example entrypoint script
```

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

1.  Fork the repository.
2.  Create a new feature branch (`git checkout -b feature/amazing-feature`).
3.  Make your changes.
4.  Run `make check-all` to ensure code quality and passing tests.
5.  Commit your changes (`git commit -m 'Add some amazing feature'`).
6.  Push to the branch (`git push origin feature/amazing-feature`).
7.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
