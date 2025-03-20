import pytest
from flask import Flask
import json
from unittest.mock import patch, MagicMock

from src.helpers.error_handlers import handle_error


@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["DEBUG"] = False

    # Push an application context so current_app can be accessed
    with app.app_context():
        yield app


@pytest.fixture
def app_debug():
    """Create a Flask app in debug mode for testing"""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["DEBUG"] = True

    with app.app_context():
        yield app


def test_handle_error_without_exception(app):
    """Test handle_error function with status code only"""
    response, status_code = handle_error(404)

    # Convert JSON response to Python dict
    data = json.loads(response.get_data(as_text=True))

    assert status_code == 404
    assert data["success"] is False
    assert data["error"]["code"] == 404
    assert data["error"]["message"] == "Not Found"
    assert "details" not in data["error"]


def test_handle_error_with_custom_message(app):
    """Test handle_error function with custom message"""
    custom_message = "Please check your request"
    response, status_code = handle_error(400, message=custom_message)

    data = json.loads(response.get_data(as_text=True))

    assert status_code == 400
    assert data["error"]["message"] == custom_message


def test_handle_error_with_exception(app):
    """Test handle_error function with exception"""
    test_error = ValueError("Test error message")

    with patch.object(app.logger, "error") as mock_logger:
        response, status_code = handle_error(500, error=test_error)

    # Verify logger was called
    mock_logger.assert_called_once()

    data = json.loads(response.get_data(as_text=True))
    assert status_code == 500
    assert data["error"]["code"] == 500
    assert data["error"]["message"] == "Internal Server Error"
    assert "details" not in data["error"]  # Since debug is False


def test_handle_error_with_exception_debug_mode(app_debug):
    """Test handle_error function with exception in debug mode"""
    # Actually raise an exception to get a real traceback
    try:
        raise ValueError("Test error message")
    except ValueError as e:
        test_error = e

        with patch.object(app_debug.logger, "error") as mock_logger:
            response, status_code = handle_error(500, error=test_error)

    # Verify logger was called
    mock_logger.assert_called_once()

    data = json.loads(response.get_data(as_text=True))
    assert status_code == 500
    assert data["error"]["code"] == 500
    assert "details" in data["error"]
    assert data["error"]["details"]["exception"] == "ValueError"
    assert data["error"]["details"]["description"] == "Test error message"
    assert data["error"]["details"]["traceback"] is not None


@patch("sys.exc_info")
def test_handle_error_with_traceback(mock_exc_info, app):
    """Test handle_error function with traceback information"""
    test_error = ValueError("Test error message")

    # Mock traceback data
    mock_traceback = MagicMock()
    mock_exc_info.return_value = (None, None, mock_traceback)

    # Mock extract_tb to return a sample frame
    with patch("traceback.extract_tb") as mock_extract_tb:
        mock_extract_tb.return_value = [("/path/to/file.py", 42, "test_function", "code_line")]

        with patch.object(app.logger, "error") as mock_logger:
            handle_error(500, error=test_error)

    # Check if logger was called with the correct message containing traceback info
    mock_logger.assert_called_once()
    log_message = mock_logger.call_args[0][0]
    assert "file: /path/to/file.py" in log_message
    assert "line: 42" in log_message
    assert "function test_function" in log_message
    assert "[ValueError]: Test error message" in log_message


def test_handle_error_unknown_status_code(app):
    """Test handle_error function with an unknown status code"""
    response, status_code = handle_error(599)

    data = json.loads(response.get_data(as_text=True))

    assert status_code == 599
    assert data["error"]["message"] == "Unknown Error"
