from rest_framework import serializers
from user.models import Users

class UserSerializer(serializers.ModelSerializer):
    class Meta():
        model = Users
        fields = ('id', 'username', 'email', 'chat_id', 'first_name', 'last_name', 'role', 'estado') 