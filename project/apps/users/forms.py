from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import Account


# standard admin form
class AccountCreationForm(UserCreationForm):
    # user_permissions = forms.ModelMultipleChoiceField(
    #     queryset=Permission.objects.all(), widget=RelatedFieldWidgetWrapper)

    class Meta(UserCreationForm):
        model = Account
        fields = ("email",)


class SignupForm(forms.ModelForm):
    """ for register with token"""

    class Meta:
        model = Account
        fields = ('email',)

    def clean(self):
        if self.Meta.model.objects.filter(email=self.cleaned_data.get('email')).exists():
            raise forms.ValidationError({'email': 'Такой пользователь уже существует'}, code="exists")


class AccountChangeForm(UserChangeForm):
    class Meta:
        model = Account
        fields = ("email",)


class AuthenticationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "name": "email",
                "placeholder": "Email"}
        ),
        label="Email",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "type": "password",
                "name": "password",
                "placeholder": "Password"}
        ),
        label="Password",
    )

    class Meta:
        fields = ["email", "password"]