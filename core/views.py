from django.shortcuts import render

# Create your views here.


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'user': {
            'email': user.email,
            'groups': user.mskuser.groups.split(',')
        }
    }
