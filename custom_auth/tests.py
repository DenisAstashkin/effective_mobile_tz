from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from rest_framework.test import APITestCase
from rest_framework import status
from .models import CustomUser, UserSession, Resource, AccessRule
from . import views

class CustomAuthAndRBACWithMockTests(APITestCase):

    def setUp(self):
        AccessRule.objects.all().delete()
        UserSession.objects.all().delete()
        Resource.objects.all().delete()
        CustomUser.objects.all().delete()

        self.doc_resource = Resource.objects.create(name='document')
        self.rules_resource = Resource.objects.create(name='access_rules')

        self.admin_user = CustomUser.objects.create(
            full_name="Главный Админ",
            email="admin@test.com",
            password_hash=make_password("admin123"),
            is_active=True
        )
        AccessRule.objects.create(user=self.admin_user, resource=self.doc_resource, is_admin_permission=True)
        AccessRule.objects.create(user=self.admin_user, resource=self.rules_resource, is_admin_permission=True)

        self.manager_user = CustomUser.objects.create(
            full_name="Менеджер Петр",
            email="manager@test.com",
            password_hash=make_password("manager123"),
            is_active=True
        )
        AccessRule.objects.create(
            user=self.manager_user, 
            resource=self.doc_resource, 
            read_all_permission=False,
            read_own_permission=True,
            create_permission=True,
            update_all_permission=False,
            update_own_permission=True,
            delete_all_permission=False,
            delete_own_permission=True
        )

        self.admin_session = UserSession.objects.create(
            user=self.admin_user,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        self.manager_session = UserSession.objects.create(
            user=self.manager_user,
            expires_at=datetime.now() + timedelta(hours=24)
        )

        self.admin_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.admin_session.token}'}
        self.manager_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.manager_session.token}'}

        views.MOCK_DOCUMENTS_DB = [
            views.MockDocument(id=1, title="Секретный план Администратора", owner_id=self.admin_user.id),
            views.MockDocument(id=2, title="Отчет по стажировке Менеджера Петра", owner_id=self.manager_user.id),
        ]

    def test_registration_success(self):
        data = {
            "full_name": "Иван Иванов",
            "email": "ivan@test.com",
            "password": "password123",
            "password_confirm": "password123"
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_password_mismatch(self):
        data = {
            "full_name": "Иван Иванов",
            "email": "ivan@test.com",
            "password": "password123",
            "password_confirm": "different"
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        data = {"email": "manager@test.com", "password": "manager123"}
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_soft_delete_account(self):
        response = self.client.delete('/api/auth/profile/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_documents_unauthorized_401(self):
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_documents_expired_token_401(self):
        from datetime import datetime, timedelta
        self.manager_session.expires_at = datetime.now() - timedelta(hours=1)
        self.manager_session.save()

        response = self.client.get('/api/documents/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_admin_can_read_all_documents(self):
        response = self.client.get('/api/documents/', **self.admin_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_manager_can_read_only_own_document(self):
        response = self.client.get('/api/documents/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['owner_id'], self.manager_user.id)

    def test_manager_cannot_update_alien_document_403(self):
        data = {"title": "Взлом"}
        response = self.client.put('/api/documents/1/', data, format='json', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_update_own_document(self):
        data = {"title": "Новое название"}
        response = self.client.put('/api/documents/2/', data, format='json', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manage_rules_forbidden_for_manager_403(self):
        response = self.client.get('/api/admin/rules/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manage_rules_success_for_admin(self):
        response = self.client.get('/api/admin/rules/', **self.admin_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_success(self):
        response = self.client.post('/api/auth/logout/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(UserSession.objects.filter(token=self.manager_session.token).exists())

    def test_get_profile_success(self):
        response = self.client.get('/api/auth/profile/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.manager_user.email)
        self.assertEqual(response.data['id'], self.manager_user.id)

    def test_update_profile_success(self):
        data = {"full_name": "Петр Петров Обновленный"}
        response = self.client.put('/api/auth/profile/', data, format='json', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.manager_user.refresh_from_db()
        self.assertEqual(self.manager_user.full_name, "Петр Петров Обновленный")

    def test_manager_can_get_own_document_detail(self):
        response = self.client.get('/api/documents/2/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 2)
        self.assertEqual(response.data['owner_id'], self.manager_user.id)

    def test_manager_cannot_get_alien_document_detail_403(self):
        response = self.client.get('/api/documents/1/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_cannot_delete_alien_document_403(self):
        response = self.client.delete('/api/documents/1/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_delete_own_document(self):
        """Менеджер может успешно удалить свой собственный документ (id=2)"""
        response = self.client.delete('/api/documents/2/', **self.manager_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        from . import views
        doc_exists = any(d.id == 2 for d in views.MOCK_DOCUMENTS_DB)
        self.assertFalse(doc_exists)

    def test_admin_can_create_access_rule(self):
        new_user = CustomUser.objects.create(
            full_name="Тестовый Юзер",
            email="user@test.com",
            password_hash=make_password("user123"),
            is_active=True
        )
        data = {
            "user": new_user.id,
            "resource": self.doc_resource.id,
            "read_all_permission": True,
            "create_permission": True
        }
        response = self.client.post('/api/admin/rules/', data, format='json', **self.admin_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AccessRule.objects.filter(user=new_user, resource=self.doc_resource).exists())
