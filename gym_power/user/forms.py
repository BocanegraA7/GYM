from django import forms
from .models import Users

class UserEditForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'password': forms.PasswordInput(render_value=True),
        }