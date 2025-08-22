# tests/unit/test_config_manager.py
import pytest
import os
import tempfile
from unittest.mock import patch, mock_open
from your_project.config_manager import ConfigManager, ConfigurationError
from your_project.models import FormConfig, FormField

class TestConfigManager:
    
    def test_load_yaml_with_env_substitution(self, monkeypatch, tmp_path):
        """Test YAML loading with environment variable substitution"""
        # Set environment variable
        monkeypatch.setenv("TEST_PASSWORD", "secret123")
        monkeypatch.setenv("TEST_URL", "https://example.com")
        
        # Create a dummy yaml file
        yaml_content = """
        url: "${TEST_URL}/form"
        fields:
          - selector: "username"
            value: "testuser"
            selector_type: "id"
            field_type: "input"
          - selector: "password"
            value: "${TEST_PASSWORD}"
            selector_type: "id"
            field_type: "input"
        submit_selector: "submit_btn"
        wait_after_fill: 2
        """
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)
        
        manager = ConfigManager()
        config = manager.load_from_yaml(str(config_file))
        
        assert config.url == "https://example.com/form"
        assert len(config.fields) == 2
        assert config.fields[0].value == "testuser"
        assert config.fields[1].value == "secret123"
        assert config.submit_selector == "submit_btn"
        assert config.wait_after_fill == 2
    
    def test_load_yaml_missing_env_variable(self, tmp_path):
        """Test YAML loading with missing environment variable"""
        yaml_content = """
        url: "${MISSING_VAR}/form"
        fields: []
        """
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)
        
        manager = ConfigManager()
        with pytest.raises(ConfigurationError, match="Environment variable MISSING_VAR not found"):
            manager.load_from_yaml(str(config_file))
    
    def test_load_yaml_invalid_format(self, tmp_path):
        """Test YAML loading with invalid format"""
        yaml_content = """
        url: "https://example.com"
        # Missing required fields
        """
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)
        
        manager = ConfigManager()
        with pytest.raises(ConfigurationError, match="Missing required field: fields"):
            manager.load_from_yaml(str(config_file))
    
    def test_load_json_with_env_substitution(self, monkeypatch, tmp_path):
        """Test JSON loading with environment variable substitution"""
        monkeypatch.setenv("API_KEY", "abc123")
        
        json_content = """{
            "url": "https://api.example.com",
            "fields": [
                {
                    "selector": "api_key",
                    "value": "${API_KEY}",
                    "selector_type": "name",
                    "field_type": "input"
                }
            ]
        }"""
        config_file = tmp_path / "config.json"
        config_file.write_text(json_content)
        
        manager = ConfigManager()
        config = manager.load_from_json(str(config_file))
        
        assert config.fields[0].value == "abc123"
    
    def test_validate_config_missing_url(self):
        """Test config validation with missing URL"""
        config_data = {
            "fields": []
        }
        
        manager = ConfigManager()
        with pytest.raises(ConfigurationError, match="Missing required field: url"):
            manager._validate_config(config_data)
    
    def test_validate_config_invalid_field(self):
        """Test config validation with invalid field"""
        config_data = {
            "url": "https://example.com",
            "fields": [
                {
                    "selector": "test",
                    # Missing required 'value' field
                    "selector_type": "id"
                }
            ]
        }
        
        manager = ConfigManager()
        with pytest.raises(ConfigurationError, match="Field missing required property: value"):
            manager._validate_config(config_data)
    
    def test_save_and_load_yaml_roundtrip(self, tmp_path):
        """Test saving and loading YAML maintains data integrity"""
        original_config = FormConfig(
            url="https://test.com",
            fields=[
                FormField(
                    selector="test_field",
                    value="test_value",
                    selector_type="id",
                    field_type="input"
                )
            ],
            submit_selector="submit"
        )
        
        config_file = tmp_path / "test_config.yaml"
        manager = ConfigManager()
        
        # Save config
        manager.save_to_yaml(original_config, str(config_file))
        
        # Load config
        loaded_config = manager.load_from_yaml(str(config_file))
        
        assert loaded_config.url == original_config.url
        assert len(loaded_config.fields) == len(original_config.fields)
        assert loaded_config.fields[0].selector == original_config.fields[0].selector
        assert loaded_config.fields[0].value == original_config.fields[0].value
        assert loaded_config.submit_selector == original_config.submit_selector

# tests/unit/test_models.py
import pytest
from your_project.models import FormField, FormConfig
from your_project.exceptions import ValidationError

class TestFormField:
    
    def test_validate_value_string(self):
        """Test string value validation"""
        field = FormField(
            selector="test",
            value="test_string",
            field_type="input"
        )
        
        assert field.validate_value() == "test_string"
    
    def test_validate_value_integer(self):
        """Test integer value validation"""
        field = FormField(
            selector="test",
            value=42,
            field_type="input"
        )
        
        assert field.validate_value() == "42"
    
    def test_validate_value_boolean_checkbox(self):
        """Test boolean value for checkbox"""
        field = FormField(
            selector="test",
            value=True,
            field_type="checkbox"
        )
        
        assert field.validate_value() == True
    
    def test_validate_value_boolean_non_checkbox(self):
        """Test boolean value for non-checkbox field"""
        field = FormField(
            selector="test",
            value=True,
            field_type="input"
        )
        
        with pytest.raises(ValidationError, match="Boolean values only allowed for checkbox and radio fields"):
            field.validate_value()
    
    def test_validate_selector_type(self):
        """Test selector type validation"""
        with pytest.raises(ValidationError, match="Invalid selector_type"):
            FormField(
                selector="test",
                value="test",
                selector_type="invalid_type"
            )
    
    def test_validate_field_type(self):
        """Test field type validation"""
        with pytest.raises(ValidationError, match="Invalid field_type"):
            FormField(
                selector="test",
                value="test",
                field_type="invalid_type"
            )
    
    def test_validate_empty_selector(self):
        """Test empty selector validation"""
        with pytest.raises(ValidationError, match="Selector cannot be empty"):
            FormField(
                selector="",
                value="test"
            )
    
    def test_validate_none_value(self):
        """Test None value validation"""
        with pytest.raises(ValidationError, match="Value cannot be None"):
            FormField(
                selector="test",
                value=None
            )

class TestFormConfig:
    
    def test_validate_empty_url(self):
        """Test empty URL validation"""
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            FormConfig(
                url="",
                fields=[]
            )
    
    def test_validate_invalid_url(self):
        """Test invalid URL validation"""
        with pytest.raises(ValidationError, match="Invalid URL format"):
            FormConfig(
                url="not-a-url",
                fields=[]
            )
    
    def test_validate_empty_fields(self):
        """Test empty fields validation"""
        with pytest.raises(ValidationError, match="At least one field must be specified"):
            FormConfig(
                url="https://example.com",
                fields=[]
            )
    
    def test_validate_negative_wait_time(self):
        """Test negative wait time validation"""
        field = FormField(selector="test", value="test")
        
        with pytest.raises(ValidationError, match="Wait times must be non-negative"):
            FormConfig(
                url="https://example.com",
                fields=[field],
                wait_after_fill=-1
            )

# tests/integration/test_selenium_form_filler.py
import pytest
import os
import tempfile
from pathlib import Path
from selenium.common.exceptions import TimeoutException
from your_project.selenium_form_filler import SeleniumFormFiller
from your_project.models import FormConfig, FormField
from your_project.exceptions import ElementNotFoundError

@pytest.fixture
def test_html_file():
    """Create a temporary HTML file for testing"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Form</title>
    </head>
    <body>
        <form id="test_form">
            <input type="text" id="text_input" name="text_field" />
            <input type="email" id="email_input" name="email_field" />
            <input type="password" id="password_input" name="password_field" />
            
            <select id="select_input" name="select_field">
                <option value="option1">Option 1</option>
                <option value="option2">Option 2</option>
                <option value="option3">Option 3</option>
            </select>
            
            <textarea id="textarea_input" name="textarea_field"></textarea>
            
            <input type="checkbox" id="checkbox_input" name="checkbox_field" />
            <label for="checkbox_input">Checkbox</label>
            
            <input type="radio" id="radio1" name="radio_field" value="radio1" />
            <label for="radio1">Radio 1</label>
            <input type="radio" id="radio2" name="radio_field" value="radio2" />
            <label for="radio2">Radio 2</label>
            
            <button type="submit" id="submit_btn">Submit</button>
        </form>
    </body>
    </html>
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        temp_file_path = f.name
    
    yield f"file://{os.path.abspath(temp_file_path)}"
    
    # Cleanup
    os.unlink(temp_file_path)

@pytest.fixture
def form_filler():
    """Create a SeleniumFormFiller instance for testing"""
    filler = SeleniumFormFiller(headless=True, timeout=5)
    yield filler
    filler.close()

class TestSeleniumFormFiller:
    
    def test_fill_text_input(self, form_filler, test_html_file):
        """Test filling a text input field"""
        config = FormConfig(
            url=test_html_file,
            fields=[
                FormField(
                    selector="text_input",
                    value="Test Text",
                    selector_type="id",
                    field_type="input"
                )
            ]
        )
        
        result = form_filler.fill_form(config)
        assert result.success == True
        
        # Verify the field was filled
        element = form_filler.driver.find_element("id", "text_input")
        assert element.get_attribute("value") == "Test Text"
    
    def test_fill_select_field(self, form_filler, test_html_file):
        """Test selecting an option in a select field"""
        config = FormConfig(
            url=test_html_file,
            fields=[
                FormField(
                    selector="select_input",
                    value="option2",
                    selector_type="id",
                    field_type="select"
                )
            ]
        )
        
        result = form_filler.fill_form(config)
        assert result.success == True
        
        # Verify the option was selected
        element = form_filler.driver.find_element("id", "select_input")
        assert element.get_attribute("value") == "option2"
    
    def test_fill_checkbox(self, form_filler, test_html_file):
        """Test checking a checkbox"""
        config = FormConfig(
            url=test_html_file,
            fields=[
                FormField(
                    selector="checkbox_input",
                    value=True,
                    selector_type="id",
                    field_type="checkbox"
                )
            ]
        )
        
        result = form_filler.fill_form(config)
        assert result.success == True
        
        # Verify the checkbox was checked
        element = form_filler.driver.find_element("id", "checkbox_input")
        assert element.is_selected() == True
    
    def test_fill_radio_button(self, form_filler, test_html_file):
        """Test selecting a radio button"""
        config = FormConfig(
            url=test_html_file,
            fields=[
                FormField(
                    selector="radio2",
                    value=True,
                    selector_type="id",
                    field_type="radio"
                )
            ]
        )
        
        result = form_filler.fill_form(config)
        assert result.success == True
        
        # Verify the radio button was selected
        element = form_filler.driver.find_element("id", "radio2")
        assert element.is_selected() == True
    
    def test_fill_multiple_fields(self, form_filler, test_html_file):
        """Test filling multiple fields in sequence"""
        config = FormConfig(
            url=test_html_file,
            fields=[
                FormField(
                    selector="text_input",
                    value="John Doe",
                    selector_type="id",
                    field_type="input"
                ),
                FormField(
                    selector="email_input",
                    value="john@example.com",
                    selector_type="id",
                    field_type="input"
                ),
                FormField(
                    selector="select_input",
                    value="option3",
                    selector_type="id",
                    field_type="select"
                ),
                FormField(
                    selector="checkbox_input",
                    value=True,
                    selector_type="id",
                    field_type="checkbox"
                )
            ]
        )
        
        result = form_filler.fill_form(config)
        assert result.success == True
        assert len(result.filled_fields) == 4
        
        # Verify all fields were filled correctly
        text_element = form_filler.driver.find_element("id", "text_input")
        assert text_element.get_attribute("value") == "John Doe"
        
        email_element = form_filler.driver.find_element("id", "email_input")
        assert email_element.get_attribute("value") == "john@example.com"
        
        select_element = form_filler.driver.find_element("id", "select_input")
        assert select_element.get_attribute("value") == "option3"
        
        checkbox_element = form_filler.driver.find_element("id", "checkbox_input")
        assert checkbox_element.is_selected() == True
    
    def test_element_not_found(self, form_filler, test_html_file):
        """Test handling of element not found scenario"""
        config = FormConfig(
            url=test_html_file,
            fields=[
                FormField(
                    selector="nonexistent_field",
                    value="test",
                    selector_type="id",
                    field_type="input"
                )
            ]
        )
        
        result = form_filler.fill_form(config)
        assert result.success == False
        assert len(result.errors) == 1
        assert "Element not found" in result.errors[0]
    
    def test_form_submission(self, form_filler, test_html_file):
        """Test form submission after filling fields"""
        config = FormConfig(
            url=test_html_file,
            fields=[
                FormField(
                    selector="text_input",
                    value="Test",
                    selector_type="id",
                    field_type="input"
                )
            ],
            submit_selector="submit_btn",
            submit_selector_type="id"
        )
        
        result = form_filler.fill_form(config)
        assert result.success == True
        assert result.submitted == True
    
    def test_screenshot_capture(self, form_filler, test_html_file, tmp_path):
        """Test screenshot capture functionality"""
        screenshot_path = tmp_path / "test_screenshot"
        
        config = FormConfig(
            url=test_html_file,
            fields=[
                FormField(
                    selector="text_input",
                    value="Test",
                    selector_type="id",
                    field_type="input"
                )
            ],
            screenshot_path=str(screenshot_path)
        )
        
        result = form_filler.fill_form(config)
        assert result.success == True
        
        # Verify screenshots were created
        assert (screenshot_path.parent / f"{screenshot_path.name}_before.png").exists()
        assert (screenshot_path.parent / f"{screenshot_path.name}_after.png").exists()
    
    def test_different_selector_types(self, form_filler, test_html_file):
        """Test different selector types (id, name, css, xpath)"""
        config = FormConfig(
            url=test_html_file,
            fields=[
                FormField(
                    selector="text_input",
                    value="Test ID",
                    selector_type="id",
                    field_type="input"
                ),
                FormField(
                    selector="email_field",
                    value="test@example.com",
                    selector_type="name",
                    field_type="input"
                ),
                FormField(
                    selector="#password_input",
                    value="password123",
                    selector_type="css",
                    field_type="input"
                ),
                FormField(
                    selector="//textarea[@id='textarea_input']",
                    value="Test message",
                    selector_type="xpath",
                    field_type="textarea"
                )
            ]
        )
        
        result = form_filler.fill_form(config)
        assert result.success == True
        assert len(result.filled_fields) == 4

# tests/integration/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture(scope="session")
def chrome_driver():
    """Create a Chrome WebDriver instance for the test session"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    yield driver
    
    driver.quit()

# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests

# requirements-dev.txt
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-mock==3.11.1
pytest-cov==4.1.0
pytest-html==3.2.0
black==23.7.0
flake8==6.0.0
mypy==1.5.0
pre-commit==3.3.3

# Makefile
.PHONY: test test-unit test-integration install-dev lint format type-check

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m "not slow"

test-integration:
	pytest tests/integration/ -v

test-coverage:
	pytest tests/ --cov=your_project --cov-report=html --cov-report=term

lint:
	flake8 your_project/ tests/

format:
	black your_project/ tests/

type-check:
	mypy your_project/

check-all: lint type-check test

# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 your_project/ tests/
    
    - name: Type check with mypy
      run: |
        mypy your_project/
    
    - name: Test with pytest
      run: |
        pytest tests/ --cov=your_project --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml