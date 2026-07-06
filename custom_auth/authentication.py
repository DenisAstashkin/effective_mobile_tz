from rest_framework.authentication import BaseAuthentication
from .models import UserSession

class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token_key = auth_header.split(' ')[1]
        try:
            session = UserSession.objects.select_related('user').get(token=token_key)
            return (session.user, token_key)
        except UserSession.DoesNotExist:
            return None
