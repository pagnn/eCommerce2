from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.views.generic import UpdateView,View
from django.conf import settings
from .forms import MarketingPreferenceUpdateForm
from .models import MarketingPreference
from .utils import Mailchimp
from .mixins import CsrfExemptMixin

MAILCHIMP_EMAIL_LIST_ID=getattr(settings,"MAILCHIMP_EMAIL_LIST_ID",None)
# Create your views here.
class MarketingPreferenceUpdateView(SuccessMessageMixin,UpdateView):
	form_class=MarketingPreferenceUpdateForm
	template_name='marketing/form.html'
	success_url='/marketing/email/'
	success_message="Your email preference has been updated."
	def dispatch(self,*args,**kwargs):
		user=self.request.user
		if not user.is_authenticated():
			return redirect("/accounts/login/?next=/marketing/email/")
		return super(MarketingPreferenceUpdateView,self).dispatch(*args,**kwargs)
	def get_context_data(self,*args,**kwargs):
		context=super(MarketingPreferenceUpdateView,self).get_context_data(*args,**kwargs)
		context['title']="Update Email Preference"
		return context
	def get_object(self):
		request=self.request
		user=request.user
		obj,created=MarketingPreference.objects.get_or_create(user=user)
		return obj
class MailchimpWebhookView(CsrfExemptMixin,View):
	def post(self,request,*args,**kwargs):
		data=request.POST
		list_id=data.get('data[list_id]')
		if str(list_id) == str(MAILCHIMP_EMAIL_LIST_ID):
			hook_type=data.get('type')
			email=data.get('data[email]')
			response_status,response=Mailchimp().check_subscription_status(email)
			sub_status=response['status']
			is_sub=None
			mailchimp_sub=None
			if sub_status == 'subscribed':
				is_sub,mailchimp_sub=(True,True)
			elif sub_status == 'unsubscribed':
				is_sub,mailchimp_sub=(False,False)
			if is_sub is not None and mailchimp_sub is not None:
				qs=MarketingPreference.objects.filter(user_email_iexact=email)
				if qs.exists():
					qs.update(subscribed=is_sub,mailchimp_subscribed=mailchimp_sub,mailchimp_msg=str(data))

		return HttpResponse('Thank you',status=200)		



