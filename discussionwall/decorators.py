from django.conf import settings
from rest_framework.response import Response
from rest_framework import status, serializers

Fail = settings.FAIL


def authorization_required(function):
    def wrap(request, *args, **kwargs):
        # uid = request.query_params.get('userId')
        # if not (uid and uid.isnumeric()):
        #     raise serializers.ValidationError("userId is required in param")
        if request.user.is_authenticated :
            print("hello")
            return function(request, *args, **kwargs)
        else:
            Fail['Comments'] = "Anonymous user"
            return Response(Fail, status=status.HTTP_401_UNAUTHORIZED)
    # wrap.__doc__ = function.__doc__
    # wrap.__name__ = function.__name__
    return wrap


# def authorization_required(function):
#     def wrap(request, *args, **kwargs):
#         if request.user.is_authenticated:
#             userId = request.query_params.get('userId')
#             if(userId == None):
#                 Fail['Comments'] = "UserId Required"
#                 return Response(Fail, status=status.HTTP_401_UNAUTHORIZED)
#             else:
#                 if(userId != request.user.id):
#                     Fail['Comments'] = "Auth Failed userId unamtch"
#                     return Response(Fail, status=status.HTTP_401_UNAUTHORIZED)
#             return function(request, *args, **kwargs)
#         else:
#             Fail['Comments'] = "Anonymous user"
#             return Response(Fail, status=status.HTTP_401_UNAUTHORIZED)
#     # wrap.__doc__ = function.__doc__
#     # wrap.__name__ = function.__name__
#     return wrap
