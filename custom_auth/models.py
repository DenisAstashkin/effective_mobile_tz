import uuid
from django.db import models
from django.utils import timezone

class CustomUser(models.Model):
    full_name = models.CharField(max_length=255, null=False)
    email = models.EmailField(max_length=255, unique=True, null=False)
    password_hash = models.CharField(max_length=255, null=False)
    is_active = models.BooleanField(default=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'
        
class UserSession(models.Model):
    token = models.CharField(max_length=64, primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=False)

    class Meta:
        db_table = 'user_sessions'

    def is_expired(self):
        return timezone.now() > self.expires_at

class Resource(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False)

    class Meta:
        db_table = 'resources'

class AccessRule(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=False)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, null=False)
    
    read_all_permission = models.BooleanField(default=False, null=False)
    read_own_permission = models.BooleanField(default=False, null=False)
    create_permission = models.BooleanField(default=False, null=False)
    update_all_permission = models.BooleanField(default=False, null=False)
    update_own_permission = models.BooleanField(default=False, null=False)
    delete_all_permission = models.BooleanField(default=False, null=False)
    delete_own_permission = models.BooleanField(default=False, null=False)
    is_admin_permission = models.BooleanField(default=False, null=False)

    class Meta:
        db_table = 'access_rules'
        unique_together = ('user', 'resource')