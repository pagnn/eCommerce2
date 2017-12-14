
from django.contrib import messages
from django.shortcuts import render,get_object_or_404,redirect
from django.views.generic import ListView,DetailView,View
from django.http import Http404,HttpResponse,HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType


from analytics.mixins import ObjectViewedMixin
from carts.models import Cart
from .models import Product
from analytics.models import ObjectViewed
# Create your views here.

class UserProductHistoryListView(LoginRequiredMixin,ListView):
	template_name='products/history.html'
	def get_queryset(self,*args,**kwargs):
		request=self.request
		views=request.user.objectviewed_set.by_model(Product)
		return views
	def get_context_data(self,*args,**kwargs):
		context=super(UserProductHistoryListView,self).get_context_data(*args,**kwargs)
		cart_obj,new_obj=Cart.objects.new_or_get(self.request)
		context['cart']=cart_obj
		return context	


class ProductListView(ListView):
	def get_queryset(self,*args,**kwargs):
		request=self.request
		return Product.objects.all()
	def get_context_data(self,*args,**kwargs):
		context=super(ProductListView,self).get_context_data(*args,**kwargs)
		cart_obj,new_obj=Cart.objects.new_or_get(self.request)
		context['cart']=cart_obj
		return context	
class ProductDetaiSlugView(ObjectViewedMixin,DetailView):
	def get_context_data(self,*args,**kwargs):
		context=super(ProductDetaiSlugView,self).get_context_data(*args,**kwargs)
		cart_obj,new_obj=Cart.objects.new_or_get(self.request)
		context['cart']=cart_obj
		print (context)
		return context
	def get_queryset(self,*args,**kwargs):
		request=self.request
		return Product.objects.all()

	def get_object(self,*args,**kwargs):
		request=self.request

		slug=self.kwargs.get('slug')

		try:
			instance=Product.objects.get(slug=slug,active=True)
		except Product.DoesNotExist:
			raise Http404('Not Found....')
		except Product.MultipleObjectsReturned:
			qs=Product.objects.filter(slug=slug,active=True)
			instance=qs.first()
		except:
			raise Http404('Uhhmmm...')
		return instance
import os
from wsgiref.util import FileWrapper
from django.conf import settings
from mimetypes import guess_type
from orders.models import ProductPurchase

class ProductDownloadView(View):
	def get(self,request,*args,**kwargs):
		slug=kwargs.get('slug')
		pk=kwargs.get('pk')
		qs=Product.objects.filter(slug=slug)
		if qs.count() != 1:
			raise Http404('Product Not Found')
		product_obj=qs.first()
		download_files=product_obj.get_downloads().filter(pk=pk)
		if download_files.count() != 1:
			raise Http404('Download Not Found')
		download_obj=download_files.first()
		can_download=False
		user_ready=True
		if download_obj.user_required:
			if not request.user.is_authenticated():
				user_ready=False		
		if download_obj.free:
			can_download=True
		else:
			purchased_products=ProductPurchase.objects.products_by_request(request)
			if product_obj in purchased_products:
				can_download=True
		if not can_download or not user_ready:
			messages.error(request,"You do not have access to this item.")
			return redirect(download_obj.get_default_url())	

		aws_filepath=download_obj.generate_download_url()
		print(aws_filepath)
		return HttpResponseRedirect(aws_filepath)
		# file_root=settings.PROTECTED_ROOT
		# filepath=download_obj.file.path
		# file_filepath=os.path.join(file_root,filepath)
		# with open(file_filepath,'rb') as f:
		# 	wrapper=FileWrapper(f)
		# 	mimetype='application/force-download'
		# 	guess_mimetype=guess_type(filepath)[0]
		# 	if guess_mimetype:
		# 		mimetype=guess_mimetype
		# 	response=HttpResponse(wrapper,content_type=mimetype)
		# 	response['Content-Disposition']='attachment;filename=%s'%(download_obj.name)
		# 	response['X-SendFile']='%s.txt'%(download_obj.name)
		# return response
		

