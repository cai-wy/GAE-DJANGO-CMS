from django.contrib import admin
from app1.models import Baseset,Category,Ads,Links,Tag,Entry

class BasesetAdmin(admin.ModelAdmin):
    list_display = ('title',)
    pass

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','sort','entrycount')
    exclude = ['post_keys']
    pass

class AdsAdmin(admin.ModelAdmin):
    list_display = ('name',)
    pass

class LinksAdmin(admin.ModelAdmin):
    list_display = ('name','sort')
    pass

class TagAdmin(admin.ModelAdmin):
    list_display = ('tag','entrycount')
    pass

class EntryAdmin(admin.ModelAdmin):
    list_display = ('title','category','pub_time')
    list_filter = ('title','category')
    search_fields = ('title','tags','abstract','content')
    ordering = ('-pub_time',)
    pass

admin.site.register(Baseset, BasesetAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Ads, AdsAdmin)
admin.site.register(Links, LinksAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Entry, EntryAdmin)
