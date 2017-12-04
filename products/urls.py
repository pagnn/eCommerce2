from django.conf.urls import url
from .views import ProductDetaiSlugView,ProductListView,ProductDownloadView

urlpatterns = [
    url(r'^$', ProductListView.as_view(),name='list'),
    url(r'^(?P<slug>[\w-]+)/$', ProductDetaiSlugView.as_view(),name='detail'),
    url(r'^(?P<slug>[\w-]+)/(?P<pk>\d+)/$', ProductDownloadView.as_view(),name='download'),
]