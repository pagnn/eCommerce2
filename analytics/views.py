from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.db.models import Sum,Count,Avg
from django.utils import timezone
import datetime
from orders.models import Order
# Create your views here.
class SalesView(LoginRequiredMixin,TemplateView):
	template_name='analytics/sales.html'
	def dispatch(self,*args,**kwargs):
		user=self.request.user
		if not user.is_staff:
			return HttpResponse(self.request,'400.html',status=401)
		return super(SalesView,self).dispatch(*args,**kwargs)
	def get_context_data(self,*args,**kwargs):
		context=super(SalesView,self).get_context_data(*args,**kwargs)
		qs=Order.objects.all()
		two_weeks_ago=timezone.now()-datetime.timedelta(days=14)
		one_week_ago=timezone.now()-datetime.timedelta(days=7)
		one_day_ago=timezone.now()-datetime.timedelta(days=1)
		context['recent_qs']=qs.by_range(start_date=one_day_ago)
		context['recent_qs_total']=context['recent_qs'].total_data()
		context['recent_qs_cart_data']=context['recent_qs'].cart_data()
		context['shipped_qs']=qs.by_status(status='shipped')[:5]
		context['shipped_qs_total']=context['shipped_qs'].total_data()
		context['shipped_qs_cart_data']=context['shipped_qs'].cart_data()		
		context['paid_qs']=qs.by_status(status='paid')[:5]
		context['paid_qs_total']=context['paid_qs'].total_data()
		context['paid_qs_cart_data']=context['paid_qs'].cart_data()			
		return context