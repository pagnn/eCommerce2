import os

AWS_GROUP_NAME='PAGNN_eCommerce_Group'
AWS_USERNAME='pagnn-ecommerce-user'
AWS_ACCESS_KEY_ID= os.environ.get('AWS_ACCESS_KEY_ID','AKIAJRUA6OMI25U7UKWA')
AWS_SECRET_ACCESS_KEY= os.environ.get('AWS_SECRET_ACCESS_KEY','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')


AWS_FILE_EXPIRE = 200
AWS_PRELOAD_METADATA = True
AWS_QUERYSTRING_AUTH = True

DEFAULT_FILE_STORAGE = 'ecommerce.aws.utils.MediaRootS3BotoStorage'
STATICFILES_STORAGE = 'ecommerce.aws.utils.StaticRootS3BotoStorage'
AWS_STORAGE_BUCKET_NAME = 'pagnn-ecommerce'
S3DIRECT_REGION = 'ap-northeast-1'
S3_URL = '//%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
MEDIA_URL = '//%s.s3.amazonaws.com/media/' % AWS_STORAGE_BUCKET_NAME
MEDIA_ROOT = MEDIA_URL
STATIC_URL = S3_URL + 'static/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'




PROTECTED_DIR_NAME = 'protected'
PROTECTED_MEDIA_URL = '//%s.s3.amazonaws.com/%s/' %( AWS_STORAGE_BUCKET_NAME, PROTECTED_DIR_NAME)

AWS_DOWNLOAD_EXPIRE = 5000 #(0ptional, in milliseconds)

import datetime

two_months = datetime.timedelta(days=61)
date_two_months_later = datetime.date.today() + two_months
expires = date_two_months_later.strftime("%A, %d %B %Y 20:00:00 GMT")

AWS_HEADERS = { 
	'Expires': expires,
	'Cache-Control': 'max-age=%d' % (int(two_months.total_seconds()), ),
}

