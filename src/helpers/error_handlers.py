from flask import jsonify, current_app
import sys
import traceback


def handle_error(status_code, error=None, message=None):
    """
    Enhanced utility function to handle errors with consistent response format
    and detailed logging

    Args:
        status_code (int): HTTP status code
        error (Exception, optional): Exception object
        message (str, optional): Custom error message

    Returns:
        tuple: (JSON response, status code)
    """
    error_messages = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        500: "Internal Server Error",
    }

    # Use custom message if provided, otherwise use default
    if message is None:
        message = error_messages.get(status_code, "Unknown Error")

    # Log detailed error information
    if error:
        error_class = error.__class__.__name__
        detail = str(error)

        # Get traceback information
        _, _, traceback_obj = sys.exc_info()
        if traceback_obj:
            last_call_stack = traceback.extract_tb(traceback_obj)[-1]
            file_name = last_call_stack[0]
            line_num = last_call_stack[1]
            func_name = last_call_stack[2]

            # Generate detailed error message
            err_msg = (
                f"Exception raised in file: {file_name}, line: {line_num}, in function {func_name},"
                f"[{error_class}]: {detail}"
            )
            current_app.logger.error(err_msg)
        else:
            current_app.logger.error(f"Error occurred: [{error_class}] {detail}")

    # Create response object
    response = {"success": False, "error": {"code": status_code, "message": message}}

    # Add error details in development mode only
    if current_app.debug and error:
        response["error"]["details"] = {
            "exception": error.__class__.__name__,
            "description": str(error),
            "traceback": traceback.format_exc().split("\n") if traceback_obj else None,
        }

    return jsonify(response), status_code
