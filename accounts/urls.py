from django.conf.urls import url
from products.views import UserProductHistoryListView
from .views import AccountHomeView,EmailActivationView,UserDetailUpdateView

urlpatterns = [
    url(r'^$',AccountHomeView.as_view(),name='home'),
    url(r'^email/confirm/(?P<key>[0-9A-Za-z]+)/$',EmailActivationView.as_view(),name='email-activate'),
    url(r'^email/resend-activation/$',EmailActivationView.as_view(),name='resend_activation'),
    url(r'^detail/$',UserDetailUpdateView.as_view(),name='user-update'),
    url(r'^history/products/$',UserProductHistoryListView.as_view(),name='history-products'),
]