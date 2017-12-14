import math
import datetime
from django.conf import settings
from django.db import models
from ecommerce.utils import unique_order_id_generator
from django.db.models.signals import pre_save,post_save
from django.core.urlresolvers import reverse
from django.db.models import Sum,Count,Avg
from django.utils import timezone

from carts.models import Cart
from billing.models import BillingProfile
from addresses.models import Address
from products.models import Product
ORDER_STATUS_CHOICES = (
	('created','Created'),
	('paid','Paid'),
	('shipped','Shipped'),
	('refunded','Refunded'),
)
# Create your models here.
class OrderManagerQuerySet(models.query.QuerySet):
	def recent(self):
		return self.order_by('updated','timestamp')
	def by_range(self,start_date,end_date=None):
		if end_date is None:
			return self.filter(updated__gte=start_date)
		return self.filter(updated__gte=start_date).filter(updated__lte=end_date)
	def by_date(self):
		return self.filter(updated__day=timezone.now().day)
	def total_data(self):
		return self.aggregate(Sum('total'),Avg('total'))
	def cart_data(self):
		return self.aggregate(Sum('cart__products__price'),Avg('cart__products__price'),Count('cart__products'))
	def by_status(self,status='shipped'):
		return self.filter(status=status)

	def by_billing_profile(self,request):
		my_profile,created=BillingProfile.objects.new_or_get(request)
		return self.filter(billing_profile=my_profile)
	def not_created(self):
		return self.exclude(status='created')
class OrderManager(models.Manager):
	def get_queryset(self):
		return OrderManagerQuerySet(self.model,using=self._db)
	def recent(self):
		return self.get_queryset().recent()
	def by_billing_profile(self,request):
		return self.get_queryset().by_billing_profile(request)
	def new_or_get(self,billing_profile,cart_obj):
		qs=self.get_queryset().filter(billing_profile=billing_profile,cart=cart_obj,active=True,status='created')
		if qs.count() == 1:
			created=False
			obj=qs.first()
		else:
			created=True
			obj=self.model.objects.create(billing_profile=billing_profile,cart=cart_obj)
		return obj,created
class Order(models.Model):
	order_id               =models.CharField(max_length=120,blank=True)
	billing_profile        =models.ForeignKey(BillingProfile,null=True,blank=True)
	shipping_address 	   =models.ForeignKey(Address,related_name='shipping_address',null=True,blank=True)
	billing_address        =models.ForeignKey(Address,name='billing_address',null=True,blank=True)
	billing_address_final  =models.TextField(blank=True,null=True)
	shipping_address_final =models.TextField(blank=True,null=True)
	cart                   =models.ForeignKey(Cart)
	status			       =models.CharField(max_length=120,default='created',choices=ORDER_STATUS_CHOICES)
	shipping_total         =models.DecimalField(decimal_places=2,max_digits=20,default=5.99)
	total      		       =models.DecimalField(decimal_places=2,max_digits=20,default=0.00)
	active                 =models.BooleanField(default=True)
	timestamp              =models.DateTimeField(auto_now_add=True)
	updated                =models.DateTimeField(auto_now=True)
	objects                =OrderManager()


	class Meta:
		ordering =['-timestamp','-updated']
	def get_absolute_url(self):
		return reverse('orders:detail',kwargs={'order_id':self.order_id})
	def get_shipping_status(self):
		if self.status == 'refunded':
			return 'Refunded'
		elif self.status == 'shipped':
			return 'Shipped'
		else:
			return 'Shipping Soon'

	def __str__(self):
		return self.order_id

	def update_total(self):
		cart_total=self.cart.total
		shipping_total=self.shipping_total
		new_total=math.fsum([cart_total,shipping_total])
		formatted_total=format(new_total,'.2f')
		self.total=formatted_total
		self.save()
		return new_total

	def check_done(self):
		shipping_address_required=not self.cart.is_digital
		billing_profile=self.billing_profile
		shipping_address=self.shipping_address
		billing_address=self.billing_address
		total=self.total
		shipping_done=False

		if shipping_address_required and shipping_address:
			shipping_done=True
		elif shipping_address_required and not shipping_address:
			shipping_done=False
		else:
			shipping_done=True

		if billing_profile and shipping_done and billing_address and total >0:
			return True
		return False
	def update_purchases(self):
		for p in self.cart.products.all():
			obj,created=ProductPurchase.objects.get_or_create(
				order_id=self.order_id,
				product=p,
				billing_profile=self.billing_profile,
			)
		return ProductPurchase.objects.filter(order_id=self.order_id).count()

	def mark_paid(self):
		if self.status != 'paid':
			if self.check_done():
				self.status='paid'
				self.save()
				self.update_purchases()
		return self.status 

def pre_save_order_receiver(sender,instance,*args,**kwargs):
	if not instance.order_id:
		instance.order_id=unique_order_id_generator(instance)
	qs=Order.objects.filter(cart=instance.cart,active=True).exclude(billing_profile=instance.billing_profile)
	if qs.exists():
		qs.update(active=False)
	if instance.shipping_address and not instance.shipping_address_final:
		instance.shipping_address_final=instance.shipping_address.get_address()
	if instance.billing_address and not instance.billing_address_final:
		instance.billing_address_final=instance.billing_address.get_address()
pre_save.connect(pre_save_order_receiver,sender=Order)

def post_save_cart_total_receiver(sender,instance,created,*args,**kwargs):
	if not created:
		cart_obj=instance
		cart_total=cart_obj.total 
		cart_id=cart_obj.id
		qs=Order.objects.filter(cart__id=cart_id)
		if qs.count() == 1:
			order_obj=qs.first()
			order_obj.update_total()
post_save.connect(post_save_cart_total_receiver,sender=Cart)


def post_save_order(sender,instance,created,*args,**kwargs):
	if created:
		instance.update_total()

post_save.connect(post_save_order,sender=Order)


class ProductPurchaseQuerySet(models.query.QuerySet):
	def by_billing_profile(self,request):
		my_profile,created=BillingProfile.objects.new_or_get(request)
		return self.filter(billing_profile=my_profile)	
	def active(self):
		return self.filter(refunded=False)
	def digital(self):
		return self.filter(product__is_digital=True)
class ProductPurchaseManager(models.Manager):
	def by_billing_profile(self,request):
		return self.get_queryset().by_billing_profile(request)	
	def get_queryset(self):
		return ProductPurchaseQuerySet(self.model,using=self._db)
	def all(self):
		return self.get_queryset().active()
	def digital(self):
		return self.get_queryset().active().digital()
	def products_by_id(self,request):
		qs=self.by_billing_profile(request).digital()
		p_ids=[p.product.id for p in qs]
		return p_ids
	def products_by_request(self,request):
		p_ids=self.products_by_id(request)
		products=Product.objects.filter(id__in=p_ids)
		return products
class ProductPurchase(models.Model):
	order_id          =models.CharField(max_length=120)
	billing_profile   =models.ForeignKey(BillingProfile,null=True,blank=True)
	product           =models.ForeignKey(Product,null=True,blank=True)
	refunded          =models.BooleanField(default=False)
	updated           =models.DateTimeField(auto_now=True)
	timestamp		  =models.DateTimeField(auto_now_add=True)

	objects           =ProductPurchaseManager()

	def __str__(self):
		return self.product.title