from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'success': False,
            'error_code': response.status_code,
            'errors': {}
        }

        if isinstance(response.data, dict):
            for key, value in response.data.items():
                if isinstance(value, list):
                    custom_response_data['errors'][key] = value[0]
                else:
                    custom_response_data['errors'][key] = value
        else:
            custom_response_data['errors']['detail'] = response.data

        response.data = custom_response_data

    return response
