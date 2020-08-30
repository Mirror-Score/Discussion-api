from rest_framework.views import *
from django.conf import settings


FAIL = settings.FAIL

def custom_exception_handler(exc, context):
    print('hello')
    """
    Returns the response that should be used for any given exception.
    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.
    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        # if isinstance(exc.detail, (list,dict)):
        #     data = exc.detail
        print(exc.detail)
        if isinstance(exc.detail, dict):
            try:    
                data = exc.detail['detail']
            except:
                data = [ele[0] for ele in exc.detail.values()]
        elif isinstance(exc.detail, list):
            # data = exc.detail
            data = exc.detail[0]
        else:
            # data = {'detail': exc.detail}
            data = exc.detail

        FAIL['Comments'] = data
        data = FAIL
        set_rollback()
        return Response(data, status=exc.status_code, headers=headers)

    return None