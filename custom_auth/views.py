from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import CustomUser, UserSession, AccessRule
from .permissions import CustomRBACPermission
from .serializers import AccessRuleSerializer

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data
        if data.get('password') != data.get('password_confirm'):
            return Response({"error": "Пароли не совпадают"}, status=400)
        if CustomUser.objects.filter(email=data.get('email')).exists():
            return Response({"error": "Email уже зарегистрирован"}, status=400)

        user = CustomUser.objects.create(
            full_name=data.get('full_name'),
            email=data.get('email'),
            password_hash=make_password(data.get('password'))
        )
        return Response({"message": "Пользователь успешно создан"}, status=201)

class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
        except CustomUser.DoesNotExist:
            return Response({"error": "Неверные учетные данные"}, status=400)

        if not check_password(password, user.password_hash):
            return Response({"error": "Неверные учетные данные"}, status=400)

        session = UserSession.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        return Response({"token": session.token}, status=200)

class ProfileView(APIView):
    def get(self, request):
        return Response({"id": request.user.id, "full_name": request.user.full_name, "email": request.user.email})

    def put(self, request):
        user = request.user
        user.full_name = request.data.get('full_name', user.full_name)
        user.save()
        return Response({"message": "Данные профиля обновлены"})

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()
        UserSession.objects.filter(user=user).delete()
        return Response({"message": "Аккаунт деактивирован (is_active=False), сессии закрыты"}, status=200)

class LogoutView(APIView):
    def post(self, request):
        
        UserSession.objects.filter(token=request.auth).delete()
        return Response({"message": "Вы успешно вышли из системы"}, status=200)

class ManageRulesView(APIView):
    permission_classes = [CustomRBACPermission]
    resource_name = 'access_rules'

    def get(self, request):
        rules = AccessRule.objects.all()
        serializer = AccessRuleSerializer(rules, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AccessRuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class MockDocument:
    def __init__(self, id, title, owner_id):
        self.id = id
        self.title = title
        self.owner_id = owner_id

MOCK_DOCUMENTS_DB = [
    MockDocument(id=1, title="Секретный план Администратора", owner_id=1),
    MockDocument(id=2, title="Отчет по стажировке Менеджера Петра", owner_id=2),
]

class MockDocumentView(APIView):
    permission_classes = [CustomRBACPermission]
    resource_name = 'document'

    def get(self, request, pk=None):
        try:
            rule = AccessRule.objects.get(user=request.user, resource__name=self.resource_name)
        except AccessRule.DoesNotExist:
            raise PermissionDenied()

        if pk is None:
            if rule.is_admin_permission or rule.read_all_permission:
                data = MOCK_DOCUMENTS_DB
            elif rule.read_own_permission:
                data = [d for d in MOCK_DOCUMENTS_DB if d.owner_id == request.user.id]
            else:
                data = []
            return Response([{"id": d.id, "title": d.title, "owner_id": d.owner_id} for d in data])
        
        else:
            doc = next((d for d in MOCK_DOCUMENTS_DB if d.id == int(pk)), None)
            if not doc:
                return Response({"error": "Документ не найден"}, status=404)
            
            self.check_object_permissions(request, doc)
            return Response({"id": doc.id, "title": doc.title, "owner_id": doc.owner_id})

    def put(self, request, pk):
        global MOCK_DOCUMENTS_DB
        
        idx = next((i for i, d in enumerate(MOCK_DOCUMENTS_DB) if d.id == int(pk)), None)
        if idx is None:
            return Response({"error": "Документ не найден"}, status=404)

        doc = MOCK_DOCUMENTS_DB[idx]

        self.check_object_permissions(request, doc)
        
        doc.title = request.data.get('title', doc.title)
        
        MOCK_DOCUMENTS_DB[idx] = doc
        
        return Response({"message": f"Документ {pk} изменен", "title": doc.title})

    def delete(self, request, pk):
        global MOCK_DOCUMENTS_DB
        doc = next((d for d in MOCK_DOCUMENTS_DB if d.id == int(pk)), None)
        if not doc:
            return Response({"error": "Документ не найден"}, status=404)

        self.check_object_permissions(request, doc)
        
        MOCK_DOCUMENTS_DB = [d for d in MOCK_DOCUMENTS_DB if d.id != int(pk)]
        return Response({"message": f"Документ {pk} успешно удален из памяти"})
