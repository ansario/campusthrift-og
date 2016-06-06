from django.contrib import admin
from models import Subcategory, Category
# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Category, CategoryAdmin)

class SubCategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Subcategory, SubCategoryAdmin)