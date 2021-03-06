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
from django.conf.urls import url
import views

urlpatterns = [

    url(r'^$', views.shop, name='shop'),
    url(r'^new$', views.new, name='new'),
    url(r'^view/(?P<pk>[0-9]+)/$', views.view_item, name="view_item"),
    url(r'^item/(?P<pk>[0-9]+)/delete$', views.delete_item, name="delete_item"),
    url(r'^cart/(?P<pk>[0-9]+)/delete$', views.cart_delete, name="delete_cart_item"),
    url(r'^category/(?P<category>\w+)/$', views.shop_category, name='shop_category'),
    url(r'category/(?P<category>.+?)/(?P<subcategory>.+?)/$', views.shop_subcategory, name='shop_subcategory'),
    url(r'^cart$', views.view_cart, name="view_cart"),

    # url(r'^')
]
