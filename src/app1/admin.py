from django.contrib import admin
from app1.models import Baseset,Category,Ads,Links

class BasesetAdmin(admin.ModelAdmin):
    list_display = ('title',)
    pass

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','sort')
    exclude = ['entrycount','post_keys']
    pass

class AdsAdmin(admin.ModelAdmin):
    list_display = ('name',)
    pass

class LinksAdmin(admin.ModelAdmin):
    list_display = ('name','sort')
    pass

admin.site.register(Baseset, BasesetAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Ads, AdsAdmin)
admin.site.register(Links, LinksAdmin)
