from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Note

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'email': {'required': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class NoteSerializer(serializers.ModelSerializer):
    # User is read-only because we automatically assign it in the view from the request
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Note
        fields = ['id', 'user', 'title', 'description', 'created_at', 'updated_at']
