from django.contrib import admin
from app1.models import Baseset,Category,Ads,Links,Tag,Entry,Feed,Document,Keyword

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

class KeywordAdmin(admin.ModelAdmin):
    list_display = ('tag',)
    pass

class EntryAdmin(admin.ModelAdmin):
    list_display = ('title','category','pub_time')
    list_filter = ('title','category')
    search_fields = ('title','tags','abstract','content')
    ordering = ('-pub_time',)
    pass

class FeedAdmin(admin.ModelAdmin):
    list_display = ('name','category','url','feed_update_time','crawl_time','last_guid',)
    list_filter = ('name','category')
    search_fields = ('name','url',)
    ordering = ('-crawl_time',)
    pass

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title','author','status','feed','link')
    list_filter = ('status',)
    search_fields = ('author','title','content',)
    pass


admin.site.register(Baseset, BasesetAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Ads, AdsAdmin)
admin.site.register(Links, LinksAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Feed, FeedAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Keyword, KeywordAdmin)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()