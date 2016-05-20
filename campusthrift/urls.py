"""campusthrift URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin
from django.conf import  settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView
import shop
import checkout
import views

urlpatterns = [



    url(r'^admin/', admin.site.urls),
    url(r'^shop/', include('shop.urls')),
    url(r'^checkout/', include('checkout.urls')),
    url(r'^register$', views.register, name='register'),
    url(r'^login$', views.user_login, name='user_login'),
    url(r'^profile$', views.profile, name='profile'),
    url(r'^profile/edit$', views.profile_edit, name="profile_edit"),
    url(r'^profile/order/view/(?P<order_number>\w+)/$', views.order_view, name="order_view"),
    url(r'^$', views.home, name='home'),
    url(r'^getdetails/', shop.views.getdetails),
    url(r'^buyer_confirm/(?P<id>\w+)/$', views.buyer_confirm, name="buyer_confirm"),
    url(r'^seller_confirm/(?P<id>\w+)/$', views.seller_confirm, name="seller_confirm"),
    # url('^u/', include('upload.urls')),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
