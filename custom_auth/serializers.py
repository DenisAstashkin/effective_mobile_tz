from rest_framework import serializers
from .models import AccessRule

class AccessRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRule
        fields = '__all__'
