import os
import random
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.db import models
from django.db.models.signals import pre_save,post_save
from django.urls import reverse
from ecommerce.aws.utils import ProtectedS3BotoStorage
from ecommerce.utils import unique_slug_generator,get_filename
from ecommerce.aws.download.utils import AWSDownload
# Create your models here.
def get_filename_ext(filepath):
	base_name = os.path.basename(filepath)
	name,ext  = os.path.splitext(base_name)
	return name,ext

def upload_image_path(instance,filename):
	new_filename=random.randint(1,3910209312)
	print (new_filename)
	name,ext=get_filename_ext(filename)
	final_filename='{new_filename}{ext}'.format(new_filename=new_filename,ext=ext)
	print (final_filename)
	return 'products/{new_filename}/{final_filename}'.format(new_filename=new_filename,final_filename=final_filename)

class ProductQuerySet(models.query.QuerySet):
	def featured(self):
		return self.filter(featured=True)
	def active(self):
		return self.filter(active=True)
	def search(self,query):
		lookups=(Q(title__icontains=query) |
		 		Q(description__icontains=query) |
		 		Q(price__icontains=query) |
		 		Q(tag__title__icontains=query))
		return self.filter(lookups).distinct()

class ProductManager(models.Manager):
	def get_queryset(self):
		return ProductQuerySet(self.model,using=self._db)
	def featureds(self):
		return self.get_queryset().featured()
	def get_by_id(self,id):
		qs=self.get_queryset().filter(id=id)
		if qs.exists():
			return qs.first()
		return None
	def search(self,query):
		
		return self.get_queryset().active().search(query)

class Product(models.Model):
	title			=models.CharField(max_length=120)
	slug            =models.SlugField(blank=True,unique=True)
	description		=models.TextField()
	price           =models.DecimalField(decimal_places=2,max_digits=20,default=39.99)
	image           =models.ImageField(upload_to=upload_image_path,null=True,blank=True)
	featured        =models.BooleanField(default=False)
	active          =models.BooleanField(default=True)
	timestamp       =models.DateTimeField(auto_now_add=True)
	is_digital      =models.BooleanField(default=False)

	objects=ProductManager()

	def get_absolute_url(self):
		#return '/products/{slug}'.format(slug=self.slug)
		return reverse("products:detail",kwargs={"slug":self.slug})
	def __str__(self):
		return self.title
	def __unicode__(self):
		return self.title
	def get_downloads(self):
		qs=self.productfile_set.all()
		return qs


def product_pre_save_receiver(sender,instance,*args,**kwargs):
	if not instance.slug:
		instance.slug=unique_slug_generator(instance)
pre_save.connect(product_pre_save_receiver,sender=Product)

def upload_product_file_loc(instance,filename):
	slug=instance.product.slug
	id_=0
	try:
		id_=instance.id
	except:
		Klass=instance.__class__
		qs=Klass.objects.all().order_by('-pk')
		id_=qs.first().id+1
	if id_ is None:
		Klass=instance.__class__
		qs=Klass.objects.all().order_by('-pk')
		if qs.exists():
			id_=qs.first().id+1
		else:
			id_=0		
	if not slug:
		slug=unique_slug_generator(instance.product)
	location="products/{slug}/{id}/".format(slug=slug,id=id_)
	return location+filename


class ProductFile(models.Model):
	product = models.ForeignKey(Product)
	name   =models.CharField(max_length=120,null=True,blank=True)
	file    =models.FileField(upload_to=upload_product_file_loc,storage=ProtectedS3BotoStorage())
	free    =models.BooleanField(default=False)
	user_required = models.BooleanField(default=False)

	@property
	def display_name(self):
		og_name=get_filename(self.file.name)
		if self.name:
			return self.name
		return og_name

	def __str__(self):
		return str(self.file.name)
	def get_default(self):
		return self.product.get_absolute_url()
	def generate_download_url(self):
		bucket =getattr(settings,'AWS_STORAGE_BUCKET_NAME')
		region = getattr(settings,'S3DIRECT_REGION')
		access_key = getattr(settings,'AWS_ACCESS_KEY_ID')
		secret_key = getattr(settings,'AWS_SECRET_ACCESS_KEY')
		if not bucket or not region or not access_key or not secret_key:
			return '/products/'
		PROTECTED_DIR_NAME = getattr(settings,'PROTECTED_DIR_NAME','protected')
		path ="{base}/{file_path}".format(base=PROTECTED_DIR_NAME,file_path=str(self.file))
		aws_dl_object =  AWSDownload(access_key, secret_key, bucket, region)
		file_url = aws_dl_object.generate_url(path) #, new_filename='New awesome file'
		return path
		
	def get_download_url(self):
		return reverse("products:download",kwargs={'slug':self.product.slug,'pk':self.pk,})