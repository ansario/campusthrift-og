from __future__ import unicode_literals

from django.apps import AppConfig
from watson import search as watson

class ShopConfig(AppConfig):
    name = 'shop'

    def ready(self):
        Item = self.get_model("Item")
        watson.register(Item)
