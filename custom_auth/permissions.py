from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from .models import AccessRule, UserSession

class CustomRBACPermission(BasePermission):
    def has_permission(self, request, view):
        
        if 'auth/register' in request.path_info or 'auth/login' in request.path_info:
            return True

        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            raise NotAuthenticated('Пользователь не авторизован (Ошибка 401)', code=401)

        token_key = auth_header.split(' ')[1]
        
        try:
            session = UserSession.objects.get(token=token_key)
        except UserSession.DoesNotExist:
            raise NotAuthenticated('Неверный токен (Ошибка 401)')

        if session.is_expired():
            session.delete()
            raise NotAuthenticated('Срок действия токена истек (Ошибка 401)')

        if not request.user or not session.user.is_active:
            raise NotAuthenticated('Пользователь не найден или деактивирован (Ошибка 401)')

        resource_name = getattr(view, 'resource_name', None)
        if not resource_name:
            return True

        try:
            rule = AccessRule.objects.get(user=request.user, resource__name=resource_name)
        except AccessRule.DoesNotExist:
            raise PermissionDenied() 

        if rule.is_admin_permission:
            return True

        if request.method == 'GET':
            if rule.read_all_permission or rule.read_own_permission:
                return True
        elif request.method == 'POST':
            if rule.create_permission:
                return True
        elif request.method in ['PUT', 'PATCH']:
            if rule.update_all_permission or rule.update_own_permission:
                return True
        elif request.method == 'DELETE':
            if rule.delete_all_permission or rule.delete_own_permission:
                return True

        raise PermissionDenied()

    def has_object_permission(self, request, view, obj):
        resource_name = getattr(view, 'resource_name', None)
        rule = AccessRule.objects.get(user=request.user, resource__name=resource_name)

        if rule.is_admin_permission:
            return True

        is_owner = hasattr(obj, 'owner_id') and obj.owner_id == request.user.id

        if request.method == 'GET':
            if rule.read_all_permission: return True
            if rule.read_own_permission and is_owner: return True
        elif request.method in ['PUT', 'PATCH']:
            if rule.update_all_permission: return True
            if rule.update_own_permission and is_owner: return True
        elif request.method == 'DELETE':
            if rule.delete_all_permission: return True
            if rule.delete_own_permission and is_owner: return True

        raise PermissionDenied()
