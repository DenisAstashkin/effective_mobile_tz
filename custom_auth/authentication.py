from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from .models import UserSession

class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        parts = auth_header.split(' ')
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed('Invalid Authorization header')

        token_key = parts[1]

        try:
            session = UserSession.objects.select_related('user').get(token=token_key)
        except UserSession.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        if session.expires_at is not None and session.expires_at < timezone.now():
            raise exceptions.AuthenticationFailed('Token has expired')

        return (session.user, token_key)

    def authenticate_header(self, request):
        return 'Bearer'