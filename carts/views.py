from django.http import JsonResponse
from django.shortcuts import render,redirect
from accounts.models import GuestEmail
from django.conf import settings
from addresses.forms import AddressCheckoutForm,AddressForm
from addresses.models import Address
from accounts.forms import LoginForm,GuestForm
from products.models import Product
from .models import Cart
from orders.models import Order
from billing.models import BillingProfile

import stripe
STRIPE_SECRET_KEY=getattr(settings,'STRIPE_SECRET_KEY','sk_test_ZP7A7uDCNapWFDAj0MFwejdR')
STRIPE_PUB_KEY=getattr(settings,'STRIPE_PUB_KEY','pk_test_OHADWNQQHJbzdqNAMtlMYOjo')
stripe.api_key=STRIPE_SECRET_KEY
# Create your views here.
def cart_api_view(request):
	cart_obj,new_obj=Cart.objects.new_or_get(request)
	json_data={
		'products':[{'name':x.title,'price':x.price,'url':x.get_absolute_url(),'id':x.id} for x in cart_obj.products.all()],
		'subtotal':cart_obj.subtotal,
		'total':cart_obj.total,
	}
	return JsonResponse(json_data)
def cart_home(request):
	cart_obj,new_obj=Cart.objects.new_or_get(request)
	return render(request,'carts/home.html',{'cart':cart_obj})

def cart_update(request):
	product_id=request.POST.get('product_id')
	if product_id is not None:
		try:
			obj=Product.objects.get(id=product_id)
		except Product.DoesNotExist:
			print('Show message to the user')
			redirect("carts:home")
		cart_obj,new_obj=Cart.objects.new_or_get(request)
		if obj in cart_obj.products.all():
			cart_obj.products.remove(obj)
			added=False
		else:
			cart_obj.products.add(obj)
			added=True
	request.session['cart_items']=cart_obj.products.count()
	if request.is_ajax():
		print('Ajax Request')
		json_data={
			'added':added,
			'removed': not added,
			'cartItemsCount':cart_obj.products.count(),
		}
		return JsonResponse(json_data)
	return redirect("carts:home")

def checkout_home(request):
	cart_obj,new_cart_obj=Cart.objects.new_or_get(request)
	order_obj=None
	if new_cart_obj or cart_obj.products.count() == 0:
		return redirect("carts:home")

	login_form=LoginForm(request=request)
	guest_form=GuestForm(request=request)
	address_form=AddressForm()

	shipping_address_required=not cart_obj.is_digital
	shipping_address_id=request.session.get('shipping_address_id',None)
	billing_address_id=request.session.get('billing_address_id',None)

	billing_profile,billing_profile_created=BillingProfile.objects.new_or_get(request)
	address_qs=None
	has_card=False
	if billing_profile is not None:
		if request.user.is_authenticated():
			address_qs=Address.objects.filter(billing_profile=billing_profile)
		order_obj,order_obj_created=Order.objects.new_or_get(billing_profile,cart_obj)	
		if shipping_address_id:
			shipping_address=Address.objects.get(id=shipping_address_id)
			order_obj.shipping_address=shipping_address
			del request.session['shipping_address_id']
		if billing_address_id:
			billing_address=Address.objects.get(id=billing_address_id)
			order_obj.billing_address=billing_address
			del request.session['billing_address_id']
		if shipping_address_id or billing_address_id:
			order_obj.save()
		has_card=billing_profile.has_card
	if request.method == 'POST':
		is_prepared=order_obj.check_done()
		if is_prepared:
			is_paid,charge_msg=billing_profile.charge(order_obj)
			if is_paid:
				order_obj.mark_paid()
				request.session['cart_items']=0
				del request.session['cart_id']
				if not billing_profile.user:
					billing_profile.set_cards_inactive()
			else:
				print(charge_msg)
				return redirect("carts:checkout")
		return redirect('carts:success')
	context={
		'object':order_obj,
		'billing_profile':billing_profile,
		'login_form':login_form,
		'guest_form':guest_form,
		'address_form':address_form,
		'address_qs':address_qs,
		'has_card':has_card,
		'publish_key':STRIPE_PUB_KEY,
		'shipping_address_required':shipping_address_required,
	}
	return render(request,'carts/checkout.html',context)


def checkout_done_view(request):
	context={}
	return render(request,'carts/checkout_done.html',context)