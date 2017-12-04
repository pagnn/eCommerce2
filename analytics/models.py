from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.db.models.signals import pre_save,post_save


from .signals import object_viewed_signal
from .utils import get_client_ip
from accounts.signals import user_logged_in_signal

User=settings.AUTH_USER_MODEL

FORCE_SESSION_TO_ONE=getattr(settings,'FORCE_SESSION_TO_ONE',False)
FORCE_INACTIVEUSER_ENDSESSION=getattr(settings,'FORCE_INACTIVEUSER_ENDSESSION',False)

class ObjectViewedQuerySet(models.query.QuerySet):
	def by_model(self,model_class,return_model=False):
		c_type=ContentType.objects.get_for_model(model_class)
		qs=self.filter(content_type=c_type)	
		if return_model:
			viewd_ids=[x.object_id for x in qs]
			return model_class.objects.filter(pk__in=viewd_ids)
		return qs

class ObjectViewedManager(models.Manager):
	def get_queryset(self):
		return ObjectViewedQuerySet(self.model,using=self._db)
	def by_model(self,model_class,return_model=False):
		return self.get_queryset().by_model(model_class,return_model=False)

class ObjectViewed(models.Model):
	user=models.ForeignKey(User,null=True,blank=True)
	ip_address=models.CharField(max_length=220,blank=True,null=True)
	content_type=models.ForeignKey(ContentType)
	object_id=models.PositiveIntegerField()
	content_object=GenericForeignKey('content_type','object_id')
	timestamp=models.DateTimeField(auto_now_add=True)

	objects=ObjectViewedManager()

	def __str__(self):
		return "%s viewd %s"%(self.content_object,self.timestamp)

	class Meta:
		ordering=['-timestamp']
		verbose_name='Object viewed'
		verbose_name_plural='Objects viewd'

def object_viewed_receiver(sender,instance,request,*args,**kwargs):
	c_type=ContentType.objects.get_for_model(sender)
	user=None
	if request.user.is_authenticated():
		user=request.user
		new_view_obj=ObjectViewed.objects.create(
				user=user,
				ip_address=get_client_ip(request),
				content_type=c_type,
				object_id=instance.id,
		)

object_viewed_signal.connect(object_viewed_receiver)

class UserSession(models.Model):
	user=models.ForeignKey(User,null=True,blank=True)
	ip_address=models.CharField(max_length=220,blank=True,null=True)
	session_key=models.CharField(max_length=100,blank=True,null=True)
	timestamp=models.DateTimeField(auto_now_add=True)
	active=models.BooleanField(default=True)
	ended=models.BooleanField(default=False)

	def __str__(self):
		return self.user.email
	def end_session(self):
		session_key=self.session_key
		try:
			Session.objects.get(pk=session_key).delete()
			self.ended=True
			self.active=False
			self.save()
		except:
			pass
		return self.ended

def post_save_user_session(sender,instance,created,*args,**kwargs):
	if created:
		qs=UserSession.objects.filter(user=instance.user,ended=False,active=True).exclude(id=instance.id)
		for i in qs:
			i.end_session()

	if not instance.active and not instance.ended:
		instance.end_session()
if FORCE_SESSION_TO_ONE:
	post_save.connect(post_save_user_session,sender=UserSession)

def post_save_user(sender,instance,created,*args,**kwargs):
	if not created:
		if instance.is_active == False:
			qs=UserSession.objects.filter(user=instance.user,ended=False,active=True).exclude(id=instance.id)
			for i in qs:
				i.end_session()

if FORCE_INACTIVEUSER_ENDSESSION:
	post_save.connect(post_save_user,sender=User)



def user_logged_in_receiver(sender,instance,request,*args,**kwargs):
	ip_address=get_client_ip(request)
	user=instance
	session_key=request.session.session_key
	UserSession.objects.create(
		user=user,
		ip_address=ip_address,
		session_key=session_key,
		)

user_logged_in_signal.connect(user_logged_in_receiver)