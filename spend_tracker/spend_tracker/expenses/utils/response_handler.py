from rest_framework.response import Response


class ResponseHandler(Response):
    """
    Thin wrapper around DRF's Response so every endpoint in the project
    returns the same JSON shape:

        { "success": bool, "message": str, "data": ..., "errors": ... }

    "data" and "errors" are omitted entirely when not provided, rather than
    being sent as null, to keep successful and failed responses lean.
    """

    def __init__(self, data=None, success=True, status=None, message=None,
                 errors=None, headers=None, content_type=None):
        payload = {'success': success}
        if message is not None:
            payload['message'] = message
        if data is not None:
            payload['data'] = data
        if errors is not None:
            payload['errors'] = errors
        super().__init__(payload, status=status, headers=headers, content_type=content_type)
