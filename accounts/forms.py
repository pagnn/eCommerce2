from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth import authenticate,login

from .signals import user_logged_in_signal
from .models import EmailActivation,GuestEmail
User=get_user_model()


class ReactiveEmailForm(forms.Form):
    email=forms.EmailField()
    def clean_email(self):
        email=self.cleaned_data.get('email')
        qs=EmailActivation.objects.email_exist(email)
        if not qs.exists():
            register_link=reverse('register')
            msg='This email does not exist.Would you like to <a href="{link}">register</a>.'.format(link=register_link)
            raise forms.ValidationError(mark_safe(msg))
        return email




class UserAdminCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email','full_name') #'full_name',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserAdminCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserDetailChangeForm(forms.ModelForm):
    full_name=forms.CharField(label='Name',required=False,widget=forms.TextInput(attrs={'class':'form-control'}))
    class Meta:
        model=User
        fields=('full_name',)

class UserAdminChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'full_name','is_active', 'admin')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]



class GuestForm(forms.ModelForm):
	class Meta:
		model=GuestEmail
		fields=('email',)
	def __init__(self,request,*args,**kwargs):
		self.request=request
		super(GuestForm,self).__init__(*args,**kwargs)
	def save(self, commit=True):
		request=self.request
		obj = super(GuestForm, self).save(commit=False)
		if commit:
			obj.save()
			request.session['guest_email_id']=obj.id
		return obj

class LoginForm(forms.Form):
	email=forms.EmailField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'username'}))
	password=forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'password'}))
	def __init__(self,request,*args,**kwargs):
		self.request=request
		super(LoginForm,self).__init__(*args,**kwargs)
	def clean(self):
		request=self.request
		data=self.cleaned_data
		email=data.get('email')
		password=data.get('password')
		qs=User.objects.filter(email=email)
		if qs.exists():
			not_active=qs.filter(is_active=False)
			if not_active.exists():
				confirmed_qs=EmailActivation.objects.filter(email=email)
				is_confirmable=confirmed_qs.confirmable().exists()
				link=reverse('accounts:resend_activation')
				resend_msg="Go to <a href='{resend_link}'>resend Activation Email</a>".format(resend_link=link)
				if is_confirmable:
					msg1='Please check your email yo confirm your account or.'+resend_msg
					raise forms.ValidationError(mark_safe(msg1))
				email_exist_qs=EmailActivation.objects.email_exist(email=email)
				if email_exist_qs.exists():
					msg2='Please Reactive your email.'+resend_msg
					raise forms.ValidationError(mark_safe(msg2))
				if not is_confirmable and not email_exist_qs.exists():
					register_link=reverse('register')
					register_msg='Go to <a href="{register_link}">register</a>'.format(register_link=register_link)
					msg3='This user is inactive.'+register_msg
					raise forms.ValidationError(mark_safe(msg3))
		user=authenticate(request,email=email,password=password)
		if user is None:
			raise forms.ValidationError('Invalid Credentials.')
		login(request,user)
		self.user=user
		user_logged_in_signal.send(user.__class__,instance=user,request=request)
		try:
			del request.session['guest_email_id']
		except:
			pass          
		return data

class RegisterForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email','full_name') #'full_name',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active=False
        if commit:
            user.save()
        return user