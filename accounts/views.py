from django.contrib.auth import authenticate,login,get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render,redirect
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe
from django.views.generic.edit import FormMixin
from django.views.generic import CreateView,FormView,DetailView,View,UpdateView
from django.contrib import messages
from django.core.urlresolvers import reverse

from ecommerce.mixins import NextUrlMixin,RequestFormAttachMixin
from .forms import LoginForm,RegisterForm,GuestForm,ReactiveEmailForm,UserDetailChangeForm
from .models import GuestEmail,EmailActivation
from .signals import user_logged_in_signal

	
class AccountHomeView(LoginRequiredMixin,DetailView):
	template_name='accounts/home.html'
	def get_object(self):
		return self.request.user

class GuestRegisterView(NextUrlMixin,RequestFormAttachMixin,CreateView):
	form_class=GuestForm
	default_url='/register/'
	def get_success_url(self):
		return self.get_next_url()

	def form_invalid(self,form):
		return redirect(self.default_url)
	

class LoginView(NextUrlMixin,RequestFormAttachMixin,FormView):
	form_class=LoginForm
	success_url='/'
	template_name='accounts/login.html'
	default_url='/'
	def form_valid(self,form):    
		next_url=self.get_next_url()
		return redirect(next_url)


User=get_user_model()

class EmailActivationView(FormMixin,View):
	success_url='/login/'
	form_class=ReactiveEmailForm
	key=None
	def get_context_data(self,*args,**kwargs):
		context = super(EmailActivationView,self).get_context_data(*args,**kwargs)
		context['form'] = self.get_form()
		return context	
	def get(self,request,key=None,*args,**kwargs):
		self.key=key
		if key is not None:
			qs=EmailActivation.objects.filter(key__iexact=key)
			confirmed_qs=qs.confirmable()
			if confirmed_qs.count() == 1:
				obj=confirmed_qs.first()
				obj.activate()
				msg="Your activation email has been confirmed.Please Login."
				messages.success(request,mark_safe(msg))
				return redirect("/login/")
			else:
				activated_qs=qs.filter(activated=True)
				if activated_qs.exists():
					reset_link=reverse("password_reset")
					msg="Your email has already been confirmed.Do you need to <a href='{link}'>reset your password</a>?".format(link=reset_link)
					messages.success(request,mark_safe(msg))
					return redirect('/login/')


		context={
			'form':self.get_form(),
			'key':key,
		}
		return render(request,'registration/emails/activate-error.html',context)
	def post(self,request,*args,**kwargs):
		form=self.get_form()
		if form.is_valid():
			return self.form_valid(form)
		else:
			return self.form_invalid(form)

	def form_valid(self,form):
		msg="Activation sent.Please check your email."
		messages.success(self.request,mark_safe(msg))
		email=form.cleaned_data.get('email')
		obj=EmailActivation.objects.email_exist(email).first()
		user=obj.user
		new_activation=EmailActivation.objects.create(user=user,email=email)
		new_activation.send_activation()
		return super(EmailActivationView,self).form_valid(form)
	def form_invalid(self,form):
		context={
			'form':self.get_form(),
			'key':self.key,
		}
		return render(self.request,'registration/emails/activate-error.html',context)
class RegisterView(CreateView):
	form_class=RegisterForm
	template_name='accounts/register.html'
	success_url="/login/"


class UserDetailUpdateView(LoginRequiredMixin,UpdateView):
	form_class=UserDetailChangeForm
	template_name='accounts/detail.html'
	def get_object(self):
		return self.request.user
	def get_context_data(self,*args,**kwargs):
		context=super(UserDetailUpdateView,self).get_context_data(*args,**kwargs)
		context['title']='Change your Detail'
		return context
	def get_success_url(self):
		return reverse('accounts:home')
