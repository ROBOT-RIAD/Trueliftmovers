from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, APIException
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from django.http import Http404
from rest_framework.response import Response




def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return Response({
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": flatten_errors(response.data)
            }
        }, status=response.status_code)
    

    if isinstance(exc, AuthenticationFailed):
        return _error("AuthenticationFailed", exc.detail, 401)

    if isinstance(exc, NotAuthenticated):
        return _error("NotAuthenticated", exc.detail, 401)

    if isinstance(exc, ValidationError):
        return _error("ValidationError", exc.message_dict, 400)
    if isinstance(exc, ObjectDoesNotExist) or isinstance(exc, Http404):
        return _error("NotFound", "Object not found", 404)
    if isinstance(exc, PermissionError):
        return _error("PermissionError", "Permission denied", 403)
    if isinstance(exc, APIException):
        return _error(exc.__class__.__name__, exc.detail, exc.status_code)

    return _error("ServerError", "Something went wrong", 500)




def _error(type, message, status_code):
    return Response({
        "success": False,
        "error": {
            "type": type,
            "message": message
        }
    }, status=status_code)





def flatten_errors(errors):
        if isinstance(errors, dict):
            messages = []
            for field, msgs in errors.items():
                if isinstance(msgs, list):
                    messages.append(f"{', '.join(msgs)}")
                else:
                    messages.append(f"{msgs}")
            return "; ".join(messages)
        elif isinstance(errors, list):
            return "; ".join(errors)
        return str(errors)
