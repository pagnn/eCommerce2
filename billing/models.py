from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save,pre_save
import stripe
from accounts.models import GuestEmail
# Create your models here.
User=settings.AUTH_USER_MODEL

STRIPE_SECRET_KEY=getattr(settings,'STRIPE_SECRET_KEY','sk_test_ZP7A7uDCNapWFDAj0MFwejdR')
stripe.api_key=STRIPE_SECRET_KEY

class BillingProfileManager(models.Manager):
	def new_or_get(self,request):
		obj=None
		created=False
		user=request.user
		guest_email_id=request.session.get('guest_email_id')
		if user.is_authenticated():
			obj,created=self.model.objects.get_or_create(user=user,email=user.email)
		elif guest_email_id is not None:
			guest_email_obj=GuestEmail.objects.get(id=guest_email_id)
			obj,created=self.model.objects.get_or_create(email=guest_email_obj.email)
		else:
			pass
		return obj,created



class BillingProfile(models.Model):
	user = models.OneToOneField(User,null=True,blank=True)
	email = models.EmailField()
	customer_id=models.CharField(max_length=120,null=True,blank=True)
	active = models.BooleanField(default=True)
	update = models.DateTimeField(auto_now=True)
	timestamp = models.DateTimeField(auto_now_add=True)
	objects = BillingProfileManager()

	def __str__(self):
		return self.email
	def charge(self,order_obj,card=None):
		return Charge.objects.do(self,order_obj,card)

	def get_cards(self):
		return self.card_set.all()
	@property
	def has_card(self):
		instance=self
		card_qs=instance.get_cards()
		return card_qs.exists()
	@property
	def default_card(self):
		default_cards=self.get_cards().filter(default=True,active=True)
		if default_cards.exists():
			return default_cards.first()
		return None
	def get_payment_method_url(self):
		return reverse("billing:pay")

	def set_cards_inactive(self):
		card_qs=self.get_cards()
		card_qs.update(active=False)
		return card_qs.filter(active=True).count()




def pre_save_billing_profile_receiver(sender,instance,*args,**kwargs):
	if not instance.customer_id and instance.email:
		customer=stripe.Customer.create(
				email=instance.email,
			)
		instance.customer_id=customer.id

pre_save.connect(pre_save_billing_profile_receiver,sender=BillingProfile)

def user_created_receiver(sender,instance,created,*args,**kwargs):
	if created:
		BillingProfile.objects.get_or_create(user=instance)
post_save.connect(user_created_receiver,sender=User)

class CardManager(models.Manager):
	def all(self,*args,**keargs):
		return self.get_queryset().filter(active=True)
	def add_new(self,billing_prfile,token):
		customer = stripe.Customer.retrieve(billing_prfile.customer_id)
		stripe_card_response=customer.sources.create(source=token)
		if str(stripe_card_response.object) == 'card':
			new_card=self.model(
				billing_prfile=billing_prfile,
				stripe_id=stripe_card_response.id,
				brand=stripe_card_response.brand,
				country=stripe_card_response.country,
				exp_month=stripe_card_response.exp_month,
				exp_year=stripe_card_response.exp_year,
				last4=stripe_card_response.last4,
				)
			new_card.save()
			return new_card
		return None

class Card(models.Model):
	billing_prfile  =models.ForeignKey(BillingProfile)
	stripe_id       =models.CharField(max_length=120,null=True,blank=True)
	brand 			=models.CharField(max_length=120,null=True,blank=True)
	country			=models.CharField(max_length=20,null=True,blank=True)
	exp_month		=models.IntegerField(null=True,blank=True)
	exp_year		=models.IntegerField(null=True,blank=True)
	last4           =models.CharField(max_length=4,null=True,blank=True)
	default         =models.BooleanField(default=True)
	active          =models.BooleanField(default=True)
	timestamp       =models.DateTimeField(auto_now_add=True)

	objects=CardManager()

	def __str__(self):
		return "{} {}".format(self.brand,self.last4)

def card_post_save_receiver(sender,instance,created,*args,**kwargs):
	if instance.default:
		billing_prfile=instance.billing_prfile
		qs=Card.objects.filter(billing_prfile=billing_prfile).exclude(pk=instance.pk)
		qs.update(default=False)
post_save.connect(card_post_save_receiver,sender=Card)

class ChargeManager(models.Manager):
	def do(self,billing_prfile,order_object,card=None):
		card_obj=card
		if card_obj is None:
			cards=billing_prfile.card_set.filter(default=True)
			if cards.exists():
				card=cards.first()
		if card is None:
			return False,"No cards available."

		c=stripe.Charge.create(
  			amount=int(order_object.total*100),
  			currency="usd",
  			customer=billing_prfile.customer_id,
  			source=card.stripe_id, # obtained with Stripe.js
  			metadata={'order_id':order_object.order_id}
		)
		new_charge_obj=self.model(
			billing_prfile=billing_prfile,
			stripe_id=c.id,
			paid=c.paid,
			refunded=c.refunded,
			outcome=c.outcome,
			outcome_type=c.outcome['type'],
			seller_message=c.outcome.get('seller_message'),
			risk_level=c.outcome.get('risk_level'),
			)
		new_charge_obj.save()
		return new_charge_obj.paid,new_charge_obj.seller_message

class Charge(models.Model):
	billing_prfile  =models.ForeignKey(BillingProfile)
	stripe_id       =models.CharField(max_length=120,null=True,blank=True)
	paid			=models.BooleanField(default=False)
	refunded		=models.BooleanField(default=False)
	outcome         =models.TextField(null=True,blank=True)
	outcome_type    =models.CharField(max_length=120,null=True,blank=True)
	seller_message	=models.CharField(max_length=120,null=True,blank=True)
	risk_level		=models.CharField(max_length=120,null=True,blank=True)

	objects=ChargeManager()

	def __str__(self):
		return "{} {}".format(self.paid,self.seller_message)