from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Convert list errors to single string
        for key, value in response.data.items():
            if isinstance(value, list) and len(value) > 0:
                response.data[key] = str(value[0])

        # Keep only the first error field
        first_key = next(iter(response.data))
        first_value = response.data[first_key]
        response.data = {first_key: first_value}

    return response
