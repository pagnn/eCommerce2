from django.conf.urls import url
from .views import payment_method_view,payment_method_create_view

urlpatterns = [
    url(r'^pay/$',payment_method_view,name='pay'),
    url(r'^pay/create/$',payment_method_create_view,name='create'),
]