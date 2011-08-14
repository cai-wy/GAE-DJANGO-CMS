# -*- coding: utf-8 -*-
from django.db.models import permalink, signals
from google.appengine.ext import db
from google.appengine.ext.db import Model as DBModel
from django.contrib.auth.models import User
from google.appengine.api import memcache
import urllib, hashlib
from ragendja.dbutils import cleanup_relations

class Baseset(db.Model):
    title = db.StringProperty(multiline=False,default='Free to me')
    subtitle = db.StringProperty(multiline=False,default='Something free to you.')
    description = db.TextProperty(default='This is a GAE app.')
    keywords = db.StringProperty(multiline=False,default='free,share')
    googlejquery = db.StringProperty(multiline=False,default='http://ajax.googleapis.com/ajax/libs/jquery/1.6.2/jquery.min.js')
    head_metas = db.TextProperty(default='')
    analytics = db.TextProperty(default='')
    admin_email = db.StringProperty(multiline=False,default='your_appID_admin@gmail.com')
    timedelta = db.FloatProperty(default=8.0)# hours
    google_cse_cx = db.StringProperty(default='009677936332633277893:-nyho-cdiwa')
    display_ngp = db.BooleanProperty(default=True)
    
    def __unicode__(self):
        return self.title

class Ads(db.Model):
    name = db.StringProperty(required=True)
    value = db.TextProperty()
    description = db.StringProperty()
    
    def __unicode__(self):
        return self.name    

class Category(db.Model):
    name = db.StringProperty(multiline=False)
    slug = db.StringProperty(multiline=False,default='')
    sort = db.IntegerProperty(default=0)
    entrycount = db.IntegerProperty(default=0)
    post_keys = db.ListProperty(db.Key)
    
    def __unicode__(self):
        return self.name
    
    @property
    def posts(self):
        men_key = "category_posts_%d"%(self.key().id())
        men_data = memcache.get(men_key)
        if men_data is None:
            men_data = db.get(self.post_keys[:10])
            memcache.add(men_key, men_data, 3600)
        return men_data
    
    @permalink
    def get_absolute_url(self):
        if self.slug:
            title = self.slug.replace(' ','_')
        else:
            title = self.name.strip()
            title = title.replace(' ','_')
            title = title.replace(',','_')
            title = title.replace(u'，','_')
            title = title.replace("/","%2f")
            title = title.replace("%","%25")        
        return ('app1.views.category_article', (), {'keyid': self.key().id(),'name':title})    

signals.pre_delete.connect(cleanup_relations, sender=Category)

class Tag(db.Model):#key_tag
    tag = db.StringProperty(multiline=False)
    entrycount = db.IntegerProperty(default=0)
    post_keys = db.ListProperty(db.Key)
    style = db.IntegerProperty(default=1)
    
    def __unicode__(self):
        return self.tag
    
    @property
    def posts(self):
        men_key = "tag_posts_%s"%(self.key().name())
        men_data = memcache.get(men_key)
        if men_data is None:
            men_data = db.get(self.post_keys[:10])
            memcache.add(men_key, men_data, 3600)
        return men_data
    
#    @permalink
#    def get_absolute_url(self):
#        if self.slug:
#            title = self.slug.replace(' ','_')
#        else:
#            title = self.name.strip()
#            title = title.replace(' ','_')
#            title = title.replace(',','_')
#            title = title.replace(u'，','_')
#            title = title.replace("/","%2f")
#            title = title.replace("%","%25")
#        return ('app1.views.tag_article', (), {'tag':self.tag})    

class Profile(db.Model):#key_email
    author = db.ReferenceProperty(User, collection_name='user_profile')
    displayname = db.StringProperty(required=True)
    email = db.EmailProperty()
    gravatar = db.StringProperty()
    web = db.StringProperty()
    aboutme = db.TextProperty()
    signtext = db.StringProperty()
    pub_ads = db.BooleanProperty(default=False)
    art_left = db.TextProperty()
    art_right = db.TextProperty()
    
    def __unicode__(self):
        return self.displayname
    
    def gravatar_url(self):
        if self.gravatar:
            return self.gravatar
        else:
            # Set your variables here
            default = 'http://www.gravatar.com/avatar/9eafa66e558d389dfdf1e7ca3d83fbb1'
            if not self.email:
                return default
            
            size = 120
        
            # construct the url
            imgurl = "http://www.gravatar.com/avatar/"
            imgurl += hashlib.md5(self.email).hexdigest()+"?"+ urllib.urlencode({'d':default, 's':str(size),'r':'G'})
            self.gravatar = imgurl
            self.put()
            return imgurl
    
    @permalink
    def get_absolute_url(self):       
        return ('app1.views.show_profile', (), {'key': self.key()})    

class BaseModel(db.Model):
    def __init__(self, parent=None, key_name=None, _app=None, **kwds):
        self.__isdirty = False
        DBModel.__init__(self, parent=None, key_name=None, _app=None, **kwds)

    def __setattr__(self,attrname,value):
        """
        DataStore api stores all prop values say "email" is stored in "_email" so
        we intercept the set attribute, see if it has changed, then check for an
        onchanged method for that property to call
        """
        if (attrname.find('_') != 0):
            if hasattr(self,'_' + attrname):
                curval = getattr(self,'_' + attrname)
                if curval != value:
                    self.__isdirty = True
                    if hasattr(self,attrname + '_onchange'):
                        getattr(self,attrname + '_onchange')(curval,value)

        DBModel.__setattr__(self,attrname,value)

class Entry(BaseModel):
    author = db.ReferenceProperty(User, collection_name='user_posts')
    author_profile = db.ReferenceProperty(Profile, collection_name='user_profile_posts')
    category = db.ReferenceProperty(Category, collection_name='cat_posts',required=True)
    title = db.StringProperty(multiline=False,default='')
    slug = db.StringProperty(multiline=False,default='')
    abstract = db.TextProperty(default='')
    content = db.TextProperty(default='')
    tags = db.StringListProperty()
    commentclosed = db.BooleanProperty(default=False)
    commentcount = db.IntegerProperty(default=0)
    comment_keys = db.ListProperty(db.Key)    
    prev_key = db.TextProperty()
    next_key = db.TextProperty()    
    pub_time = db.DateTimeProperty()
    
    def __unicode__(self):
        return self.title    
    
    @property
    def author_name(self):
        email = str(self.author)
        try:
            name = email.split('@')[0]
        except:
            name = email
        userprofile = Profile.get_or_insert(u"key_%s"%email, author = self.author,displayname = name ,email = email)
        return userprofile.displayname
    
    @property
    def profile(self):
        if self.author_profile:
            return self.author_profile
        else:
            email = str(self.author)
            try:
                name = email.split('@')[0]
            except:
                name = email
            userprofile = Profile.get_or_insert(u"key_%s"%email, author = self.author, displayname = name ,email = email)
            self.author_profile = userprofile
            self.put()
            return userprofile
        
    @property
    def comments(self):
        men_key = "article_comment_%d"%(self.key().id())
        men_data = memcache.get(men_key)
        if men_data is None:
            men_data = db.get(self.comment_keys[:10])
            memcache.add(men_key, men_data, 3600)
        return men_data
        
    @property
    def relateposts(self):
        men_key = "article_relateposts_%d"%(self.key().id())
        men_data = memcache.get(men_key)
        #men_data = None
        if men_data is None:
            tag_key_list = []
            for tag in self.tags:
                tag_obj = Tag.get_by_key_name(u"key_%s"%tag)
                tag_key_list += tag_obj.post_keys
            tag_key_list = list(set(tag_key_list))
            try:tag_key_list.remove(self.key())
            except:pass
            men_data = db.get(tag_key_list[:10])
            try:men_data.remove(None)
            except:pass
            memcache.add(men_key, men_data, 3600)
        return men_data
        
    @property
    def strtags(self):
        return ','.join(self.tags)
        
    @permalink
    def get_absolute_url(self):
        if self.slug:
            title = self.slug.replace(' ','_')
        else:
            title = self.title.strip()
            title = title.replace(' ','_')
            title = title.replace(',','_')
            title = title.replace(u'，','_')
            title = title.replace("/","%2f")
            title = title.replace("%","%25")        
        return ('app1.views.show_article', (), {'keyid': self.key().id(),'title':title})
    
    @permalink
    def short_url(self):
        return ('app1.views.show_article_short', (), {'keyid': self.key().id()})
    
    @property
    def next(self):
        if self.next_key:
            art = Entry.get(self.next_key)
            if art:
                return art
            else:
                self.next_key = None
                self.put()
                memcache.delete("article_post_%d"%self.key().id())
                return None
        else:
            art = Entry.all().order('pub_time').filter('pub_time >',self.pub_time).get()
            if art:
                self.next_key = str(art.key())
                self.put()
                memcache.delete("article_post_%d"%self.key().id())
                return art
            else:
                return None
    
    @property
    def prev(self):
        if self.prev_key:
            art = Entry.get(self.prev_key)
            if art:
                return art
            else:
                self.prev_key = None
                self.put()
                memcache.delete("article_post_%d"%self.key().id())
                return None
        else:
            art = Entry.all().order('-pub_time').filter('pub_time <',self.pub_time).get()
            if art:
                self.prev_key = str(art.key())
                self.put()
                memcache.delete("article_post_%d"%self.key().id())
                return art
            else:
                return None    

signals.pre_delete.connect(cleanup_relations, sender=Entry)

class Comment(db.Model):
    entry = db.ReferenceProperty(Entry, collection_name='post_comment')
    date = db.DateTimeProperty(auto_now_add=True)
    message = db.TextProperty(required=True)
    name = db.StringProperty(required=True)
    email = db.EmailProperty()
    web = db.StringProperty()
    gravatar = db.StringProperty()
    
    def __unicode__(self):
        return self.name 
        
    def gravatar_url(self):
        if self.gravatar:
            return self.gravatar
        else:
            # Set your variables here
            default = 'http://www.gravatar.com/avatar/9eafa66e558d389dfdf1e7ca3d83fbb1'
            if not self.email:
                return default
        
            size = 60
        
            # construct the url
            imgurl = "http://www.gravatar.com/avatar/"
            imgurl += hashlib.md5(self.email).hexdigest()+"?"+ urllib.urlencode({'d':default, 's':str(size),'r':'G'})
            self.gravatar = imgurl
            self.put()
            return imgurl

class Links(db.Model):
    sort = db.IntegerProperty(default=0)
    name = db.StringProperty(required=True)
    url = db.StringProperty(required=True,default='http://')
    
    def __unicode__(self):
        return self.name
    
############
g_blog = None
def gblog_init():
    global g_blog
    g_blog = Baseset.get_or_insert(u'default')
    gdcms = Links.get_or_insert(u'default',sort = 100, name = "GD-cms", url = "http://gae-django-cms.appspot.com")

gblog_init()
