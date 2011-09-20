# -*- coding: utf-8 -*-
import datetime
import random
from django.core.urlresolvers import reverse
from google.appengine.api import urlfetch
from app1.feedparser import *
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from app1.html2text import html2text
from google.appengine.dist import use_library
from django.contrib.auth.models import User
from google.appengine.api import users
from django.http import HttpResponse, Http404, HttpResponseRedirect
from google.appengine.ext import db
from app1.forms import *
from app1.models import *
from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site, RequestSite
from google.appengine.api.prospective_search import *
from django.utils.translation import ugettext_lazy as _, ugettext as __

from google.appengine.api import memcache
import re
import logging

cur_app = "app1"

###
categories_key = "key_all_categories"
tags_key = "key_popular_tags"
memtime=3600

###
base_values = {}
base_values['g_blog'] = g_blog

###
def del_html(con):
    p = re.compile( '<script.*?</script>')
    con = p.sub( '', con)
    con = con.strip()
    p = re.compile( '[\s]{2,}')
    con = p.sub( ' ', con)    
    p = re.compile( '<[^>]*>')
    return p.sub( '', con)

##############
def get_current_site(request):
    try:
        current_site = Site.objects.get_current()
    except:
        current_site = RequestSite(request)
    return current_site

def now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours =+ g_blog.timedelta)
    #return datetime.datetime.utcnow()

def get_categories():
    """get all categories"""
    objects = memcache.get(categories_key)
    if objects is None:
        objects = Category.all().order('-entrycount').fetch(20)
        if len(objects)==0:
            newobj = Category(name = "Default Category 1").put()
            newobj = Category(name = "Default Category 2").put()
            objects = Category.all().order('-entrycount').fetch(2)
        memcache.add(categories_key, objects,memtime)
    base_values['all_categories'] = objects
    return objects

#get_categories()

def get_tags():
    """get popular tags"""
    objects = memcache.get(tags_key)
    if objects is None:
        objects = Tag.all().order('-entrycount').fetch(40)
        if len(objects)==0:
            newobj = Tag(tag = "finance", entrycount = 1).put()
            newobj = Tag(tag = "guide", entrycount = 1).put()
            objects = Tag.all().order('-entrycount').fetch(2)
        maxcount = objects[0].entrycount
        mincount = objects[len(objects) - 1].entrycount
        distrib = (maxcount - mincount) / 5
        if distrib == 0: 
            distrib = 1
        for each in objects:
            each.style = (each.entrycount - mincount)/distrib + 1
        memcache.add(tags_key, objects, memtime)
    random.shuffle(objects)
    base_values['popular_tags'] = objects
    return objects

#get_tags()

def gae_ads():
    objects = memcache.get("all_ads_key")
    if objects is None:
        objects = Ads.all().fetch(20)
        if objects:
            pass
        else:
            updata = []
            updata.append(Ads(name = "index_focus_slideshow", value = '<img src="/media/tmp/336x280.jpg"/>', description = "index left top Focus Images,best size is 336x280px"))
            db.put(updata)
            objects = updata
        memcache.add("all_ads_key", objects,memtime*3)
    for each in objects:
        base_values['ads_%s'%each.name] = each.value
    return objects    

gae_ads()

def get_newposts():
    men_key = "newposts_key"
    objs = memcache.get(men_key)
    if objs is None:
        objs = Entry.all().order('-pub_time').fetch(10)
        memcache.add(men_key, objs, 3600)
    base_values['newpost_list'] = objs
    return objs

def get_lastcomments():
    men_key = "newcomments_key"
    objs = memcache.get(men_key)
    if objs is None:
        objs = Comment.all().order('-date').fetch(10)
        memcache.add(men_key, objs, 3600)
    base_values['newcomment_list'] = objs
    return objs

def get_links():
    men_key = "links_key"
    objs = memcache.get(men_key)
    if objs is None:
        objs = Links.all().order('-sort').fetch(20)
        memcache.add(men_key, objs, 71200)
    base_values['links_list'] = objs
    return objs
#get_links()

def checkup():
    new0 = []
    new1 = list(base_values['links_list'])
    s1 = ''.join(map(chr,[71,68,45,99,109,115]))
    s2 = ''.join(map(chr,[104,116,116,112,58,47,47,103,97,101,45,100,106,97,110,103,111,45,99,109,115,46,97,112,112,115,112,111,116,46,99,111,109]))
    get_n = True
    for n in new1:
        if n.name == s1 and (n.url == s2 or n.url[:-1] == s2):
            get_n = False
            break
    if get_n:
        new0.append({'sort': 100, 'name': s1, 'url': s2})
    new0.extend(new1)
    base_values['links_list'] = new0

#checkup()

##############
def generate(request, template_name, template_values={}):
    base_values['current_site'] = get_current_site(request)
    get_categories()
    get_lastcomments()
    get_tags()
    #
    base_values.update(template_values)
    return render_to_response(request,"%s/%s"%(cur_app,template_name),base_values)

def index(request):
    gae_ads()
    newposts = get_newposts()
    return generate(request,'index.html',{'newposts':newposts})

def paginator(page = 1,all_count = 1,page_num = 10):
    all_pages = all_count/page_num
    if all_count%page_num != 0:
        all_pages += 1
    try:page_number = int(page)
    except:page_number = 1
    if page_number < 1:
        page_number = 1
    elif page_number > all_pages:
        page_number = all_pages
    #
    page_dic = {}
    page_dic['from'] = (page_number-1)*page_num
    page_dic['to'] = page_number*page_num
    page_dic['page_number'] = page_number
    #
    plist = []
    plist.append('<div class="pagination">')
    if page_number == 1:
        plist.append('<span class="disabled"><<</span>')
    else:
        plist.append('<a href="?page=1"><<</a>')   
    if all_pages <=10:
        for i in range(1,all_pages+1):
            if i == page_number:
                plist.append('<span class="current">%d</span>'%i)
            else:
                plist.append('<a href="?page=%d">%d</a>'%(i,i))
    else:
        fromp = page_number - 5
        if fromp <=0:
            fromp = 1
        top = fromp + 10
        if top > all_pages:
            top = all_pages
        for i in range(fromp,top+1):
            if i == page_number:
                plist.append('<span class="current">%d</span>'%i)
            else:
                plist.append('<a href="?page=%d">%d</a>'%(i,i))            
    #
    if page_number == all_pages:
        plist.append('<span class="disabled">>></span>')
    else:
        plist.append('<a href="?page=%d">>></a>'%all_pages)     
    plist.append('</div>')
    page_dic['pagination_div'] = ''.join(plist)
    return page_dic
    
def category_article(request,keyid,name):
    try:keyid = int(keyid)
    except:return HttpResponseRedirect("/")
    obj = Category.get_by_id(keyid)
    if obj:
        pagination_div = None
        if obj.entrycount >10:
            page = request.GET.get('page', 1)
            try:page = int(page)
            except:page = 1
            pdic = paginator(page,obj.entrycount)
            if page == 1:
                cur_articlelist = obj.posts
            else:
                men_key = "category_posts_%d_page_%d"%(obj.key().id(),page)
                cur_articlelist = memcache.get(men_key)
                if cur_articlelist is None:
                    cur_articlelist = db.get(obj.post_keys[pdic['from']:pdic['to']])
                    memcache.add(men_key, cur_articlelist, 3600)
            pagination_div = pdic['pagination_div']            
        else:
            cur_articlelist = obj.posts
        #if len(cur_articlelist)==1:
        #    return HttpResponseRedirect(cur_articlelist[0].get_absolute_url())
        return generate(request,'articlelist.html',{'obj':obj,'cur_articlelist':cur_articlelist,'pagination_div':pagination_div})        
    else:
        return HttpResponseRedirect("/")

@login_required
def myarticles(request):
    cur_articlelist = request.user.user_posts.order("-pub_time")[:20]
    return generate(request,'myarticlelist.html',{'cur_articlelist':cur_articlelist})

def tag_article(request,tag):
    obj = Tag.get_by_key_name(u"key_%s"%tag)
    if obj:
        pagination_div = None
        if obj.entrycount >10:
            page = request.GET.get('page', 1)
            try: page = int(page)
            except: page = 1
            pdic = paginator(page,obj.entrycount)
            men_key = "tag_posts_%s_page_%d"%(obj.key(), page )
            cur_articlelist = memcache.get(men_key)
            if cur_articlelist is None:
                cur_articlelist = db.get(obj.post_keys[pdic['from']:pdic['to']])
                memcache.add(men_key, cur_articlelist, 3600)
            pagination_div = pdic['pagination_div']            
        else:
            cur_articlelist = obj.posts        
        #if len(cur_articlelist)==1:
        #    return HttpResponseRedirect(cur_articlelist[0].get_absolute_url())
        return generate(request,'articlelist.html',{'obj':obj,'cur_articlelist':cur_articlelist,'pagination_div':pagination_div})        
    else:
        return HttpResponseRedirect("/")

###
def show_article_short(request,keyid):
    if "/" in keyid:
        keyid = keyid.replace("/","")
    try:keyid = int(keyid)
    except:return HttpResponseRedirect("/")
    return HttpResponseRedirect(reverse('app1.views.show_article', kwargs=dict(keyid=keyid,title=g_blog.title)))

def show_article(request,keyid,title = g_blog.title):
    try:keyid = int(keyid)
    except:return HttpResponseRedirect("/")
    men_key = "article_post_%d"%(keyid)
    obj = memcache.get(men_key)
    if obj is None:
        obj = Entry.get_by_id(keyid)
        memcache.add(men_key, obj, 3600)
    continue_url = ''
    if obj:
        pagination_div = None
        if request.method == 'POST' and request.user.is_authenticated() and not obj.commentclosed:
            cf = CommentForm(request.POST)
            if cf.is_valid():
                cd = cf.clean()#cleaned_data
                post_now = now()
                comobj = Comment(entry = obj,
                        date = post_now,
                        message = cd['message'],
                        name = cd['name'],
                        web = cd['web'],
                        email = str(request.user)
                        )
                comobj.put()
                if comobj.is_saved():
                    uprofile = Profile.get_or_insert(u"key_%s"%comobj.email, author = request.user, displayname = comobj.name ,email = comobj.email)
                    if comobj.key() not in obj.comment_keys:
                        obj.commentcount += 1
                        obj.comment_keys.insert(0,comobj.key())
                        if obj.commentcount >= 999:
                            obj.commentclosed = True
                        obj.put()
                        #
                        memcache.delete("article_post_%d"%(obj.key().id()))
                        memcache.delete("article_comment_%d"%(obj.key().id()))
                        if obj.commentcount >=10:
                            allpage = (obj.commentcount+1)/10 + 1
                            for p in range(1,allpage+1):
                                memcache.delete("article_comment_%d_page_%d"%(obj.key().id(),p))
                        memcache.delete("newcomments_key")
                    #
                    if g_blog.admin_email:
                        current_site = get_current_site(request)
                        subject = _(u'New comment on your post <%s>')%obj.title
                        sbody = _(u'#Re: %s\n%s\n\nClick here to view it: %s')
                        #
                        tolist = [g_blog.admin_email]
                        toID = request.POST.get('toID','')
                        if toID:
                            tocomobj = Comment.get(toID)
                            if tocomobj:
                                if tocomobj.email:
                                    tolist.append(tocomobj.email)
                            else:
                                tocomobj.message = ' '
                            sbody = sbody%(obj.title,tocomobj.message,"http://%s%s#%d"%(current_site.domain,obj.short_url(),comobj.key().id()))
                        else:
                            sbody = sbody%(obj.title,obj.abstract,"http://%s%s#%d"%(current_site.domain,obj.short_url(),comobj.key().id()))
                        #
                        if str(obj.author):
                            tolist.append(str(obj.author))
                        
                        from django.core.mail import send_mail
                        try:
                            if len(tolist)==1 and g_blog.admin_email == tolist[0]:
                                pass
                            else:
                                send_mail(subject, sbody.encode('utf8'), g_blog.admin_email, tolist)
                        except:pass
                        #return generate(request,'tip.html',{'tip':sbody})
                    return HttpResponseRedirect("%s#comments"%obj.get_absolute_url())
        else:
            if request.user.is_authenticated():
                userprofile = Profile.get_by_key_name(u"key_%s"%str(request.user))
                if userprofile:
                    name = userprofile.displayname
                    web = userprofile.web
                else:
                    try:name = str(request.user).split('@')[0]
                    except:name = str(request.user)
                    web = ''
            else:
                continue_url = users.create_login_url(u"%s#postcomment"%obj.get_absolute_url())
                name = ''
                web = ''
            cf = CommentForm(initial = {'name':name,'web':web})
        ###
        if obj.commentcount >10:
            page = request.GET.get('page', 1)
            try:page = int(page)
            except:page == 1
            pdic = paginator(page,obj.commentcount)
            men_key = "article_comment_%d_page_%d"%(obj.key().id(),page)
            commentlist = memcache.get(men_key)
            if commentlist is None:
                commentlist = db.get(obj.comment_keys[pdic['from']:pdic['to']])
                memcache.add(men_key, commentlist, 3600)
            pagination_div = pdic['pagination_div']            
        else:
            commentlist = obj.comments            
        return generate(request,'detail.html',{'obj':obj,'continue_url':continue_url,'form':cf,'commentlist':commentlist,'pagination_div':pagination_div})
    else:
        return HttpResponseRedirect("/")

def settag(tagsstr):
    if tagsstr:
        tagsstr = del_html(tagsstr)
        if tagsstr:
            tagsstr = tagsstr.lower()
            tagsstr = tagsstr.replace(u"，",",")
            tagsstr = tagsstr.replace("/",",")
            tagsstr = tagsstr.replace("%",",")
            tagslist = map((lambda x: x.strip()),tagsstr.split(','))
            tagslist = list(set(tagslist))
            try:tagslist.remove('')
            except:pass
            return tagslist
        else:
            return []
    else:
        return []

@login_required
def add_article(request):
    tags = ''
    obj = None
    if request.method == 'POST':
        ef = EntryForm(request.POST)
        tags = request.POST.get('tags','')
        if ef.is_valid():            
            tagslist = settag(tags)
            cd = ef.cleaned_data
            #check exist
            title = cd['title'].strip()
            arttitle_exist = Entry.all().filter('title =', title).get()
            if arttitle_exist:
                return generate(request,'tip.html',{'tip':"title exist."})
            #
            abstract = del_html(cd['abstract'])
            if abstract == '':
                abstract = del_html(cd['content'])[:300] + " ..."
            #
            post_now = now()
            obj = Entry(author = request.user,
                title = title,
                category = cd['category'],
                abstract = abstract,
                content = cd['content'].replace("<p>&nbsp;</p>",""),
                slug = cd['slug'],
                commentclosed = cd['commentclosed'],
                tags = tagslist,
                pub_time = post_now
                )
            obj.put()
            if obj.is_saved():
                #Category
                cat = obj.category
                if obj.key() not in cat.post_keys:
                    cat.post_keys.insert(0,obj.key())
                    if cat.entrycount >= 999:
                        cat.post_keys = cat.post_keys[:999]
                    cat.entrycount = len(cat.post_keys)
                    cat.put()
                #tags
                if obj.tags:
                    for tag in obj.tags:
                        tag_obj = Tag.get_or_insert(u"key_%s"%tag,tag = tag, entrycount = 1, post_keys = [obj.key()])
                        if obj.key() not in tag_obj.post_keys:
                            tag_obj.post_keys.insert(0,obj.key())
                            if tag_obj.entrycount >= 999:
                                tag_obj.post_keys = tag_obj.post_keys[:999]
                            tag_obj.entrycount = len(tag_obj.post_keys)
                            tag_obj.put()
                #removecache
                memcache.delete("%s_rsslatest_men_%s"%(cur_app,get_current_site(request).domain))
                memcache.delete("newposts_key")
                memcache.delete("category_posts_%d"%(obj.category.key().id()))
                if obj.category.entrycount >=10:
                    allpage = (obj.category.entrycount+1)/10 + 1
                    for p in range(1,allpage+1):
                        memcache.delete("category_posts_%d_page_%d"%(obj.category.key().id(),p))                
                for tag in obj.tags:
                    memcache.delete(u"tag_posts_key_%s"%(tag))                
            return HttpResponseRedirect(reverse('app1.views.show_article', kwargs=dict(keyid=obj.key().id(),title=obj.title)))
    else:
        ef = EntryForm()
    return generate(request,'add_article.html',{'obj':obj,'form':ef,'tags':tags})

@login_required
def edit_article(request,key):
    obj = Entry.get(key)
    if not obj:
        return generate(request,'tip.html',{'tip':"your request object not exist."})
    if obj.author != request.user:
        if not request.user.is_superuser:
            HttpResponseRedirect("/")
    tags = ''
    if request.method == 'POST':
        ef = EntryForm(request.POST)
        tags = request.POST.get('tags','')
        if ef.is_valid():
            tagslist = settag(tags)
            cd = ef.cleaned_data
            old_tags = obj.tags
            obj.title = cd['title'].strip()
            oldcate = obj.category
            obj.category = cd['category']
            #
            abstract = del_html(cd['abstract'])
            if abstract == '':
                abstract = del_html(cd['content'])[:300] + " ..."
            #            
            obj.abstract = abstract
            obj.content = cd['content'].replace("<p>&nbsp;</p>","")
            obj.slug = cd['slug']
            obj.commentclosed = cd['commentclosed']
            obj.tags = tagslist
            obj.put()
            if obj.is_saved():
                if oldcate != obj.category:
                    #old
                    if obj.key() in oldcate.post_keys:
                        oldcate.post_keys.remove(obj.key())
                        oldcate.entrycount -= 1
                        oldcate.put()
                        memcache.delete("category_posts_%d"%(oldcate.key().id()))
                        if oldcate.entrycount >=10:
                            allpage = (oldcate.entrycount+1)/10 + 1
                            for p in range(1,allpage+1):
                                memcache.delete("category_posts_%d_page_%d"%(oldcate.key().id(),p))
                    #new
                    cat = obj.category
                    if obj.key() not in cat.post_keys:
                        cat.post_keys.insert(0,obj.key())
                        if cat.entrycount >= 999:
                            cat.post_keys = cat.post_keys[:999]
                        cat.entrycount = len(cat.post_keys)
                        cat.put()
                        memcache.delete("category_posts_%d"%(cat.key().id()))
                        if cat.entrycount >=10:
                            allpage = (cat.entrycount+1)/10 + 1
                            for p in range(1,allpage+1):
                                memcache.delete("category_posts_%d_page_%d"%(cat.key().id(),p))                        
                if tagslist != old_tags:
                    #remove_tags
                    for i in old_tags:
                        if i not in tagslist:
                            tg = Tag.get_by_key_name(u"key_%s"%i)
                            if tg:
                                if tg.entrycount >1:
                                    tg.entrycount -= 1
                                    try:tg.post_keys.remove(obj.key())
                                    except:pass
                                    tg.put()
                                else:
                                    tg.delete()
                                memcache.delete(u"tag_posts_key_%s"%(i))                            
                    #add_tags
                    for i in tagslist:
                        if i not in old_tags:
                            tg = Tag.get_or_insert(u"key_%s"%i,tag = i, entrycount = 1, post_keys = [obj.key()])
                            if obj.key() not in tg.post_keys:
                                tg.post_keys.insert(0,obj.key())
                                if tg.entrycount >= 999:
                                    tg.post_keys = tg.post_keys[:999]
                                tg.entrycount = len(tg.post_keys)
                                tg.put()
                                memcache.delete(u"tag_posts_key_%s"%(i))
                #removecache
                #Category#obj
                memcache.delete("newposts_key")
                memcache.delete("category_posts_%d"%(obj.category.key().id()))
                if obj.category.entrycount >=10:
                    allpage = (obj.category.entrycount+1)/10 + 1
                    for p in range(1,allpage+1):
                        memcache.delete("category_posts_%d_page_%d"%(obj.category.key().id(),p))                
                memcache.delete("article_relateposts_%d"%(obj.key().id()))
                memcache.delete("article_post_%d"%(obj.key().id()))
            return HttpResponseRedirect(reverse('app1.views.show_article', kwargs=dict(keyid=obj.key().id(),title=obj.title)))
    else:
        tags = obj.strtags
        ef = EntryForm(instance=obj)
    return generate(request,'add_article.html',{'form':ef,'tags':tags})

@login_required
def del_article(request,key):
    obj = Entry.get(key)
    if not obj:
        return generate(request,'tip.html',{'tip':"your request object not exist."})
    if obj.author != request.user:
        if not request.user.is_superuser:
            HttpResponseRedirect("/")
    if request.method == 'POST':
        #Category
        if obj.key() in obj.category.post_keys:
            obj.category.post_keys.remove(obj.key())
            obj.category.entrycount -= 1
            obj.category.put()
        #tags
        if obj.tags:
            for tag in obj.tags:
                tag_obj = Tag.get_by_key_name(u"key_%s"%tag)
                if tag_obj and obj.key() in tag_obj.post_keys:
                    tag_obj.post_keys.remove(obj.key())
                    if tag_obj.entrycount >1:
                        tag_obj.entrycount -= 1
                        tag_obj.put()
                    else:
                        tag_obj.delete()
                    memcache.delete(u"tag_posts_key_%s"%(tag))
        #comments
        if obj.comment_keys:
            db.delete(obj.comment_keys)
            memcache.delete("newcomments_key")
        #removecache
        memcache.delete("newposts_key")
        memcache.delete("category_posts_%d"%(obj.category.key().id()))
        if obj.category.entrycount >=9:
            allpage = (obj.category.entrycount+1)/10 + 1
            for p in range(1,allpage+1):
                memcache.delete("category_posts_%d_page_%d"%(obj.category.key().id(),p))
        memcache.delete("article_relateposts_%d"%(obj.key().id()))
        memcache.delete("article_post_%d"%(obj.key().id()))
        #
        obj.delete()
        return generate(request,'tip.html',{'tip':"your object has been deleted."})
    else:
        return generate(request,'delete_article.html',{'obj':obj})

@login_required
def lastcomments(request):
    if request.user.is_superuser :
        objs = get_lastcomments()
        return generate(request,'lastcomments.html',{'objs':objs})
    else:
        return generate(request,'tip.html',{'tip':u'You do not have permission to operate.'})

def del_comment(request,key):
    if request.user.is_superuser :
        obj = Comment.get(key)
        if obj:
            if obj.key() in obj.entry.comment_keys:
                obj.entry.comment_keys.remove(obj.key())
                obj.entry.commentcount -= 1
                obj.entry.put()
                memcache.delete("article_comment_%d"%(obj.entry.key().id()))
                memcache.delete("article_post_%d"%(obj.entry.key().id()))
                if obj.entry.commentcount >=9:
                    allpage = (obj.entry.commentcount+1)/10 + 1
                    for p in range(1,allpage+1):
                        memcache.delete("article_comment_%d_page_%d"%(obj.entry.key().id(),p))
                obj.delete()
                memcache.delete("newcomments_key")
            return generate(request,'tip.html',{'tip':"your object has been deleted."})
        else:
            return generate(request,'tip.html',{'tip':"your request object not exist."})
    else:
        return generate(request,'tip.html',{'tip':u'You do not have permission to operate.'})
    
@login_required
def emptymem(request):
    if request.user.is_superuser :
        memcache.flush_all()
        #
        gae_ads()
        get_links()
        checkup()
        global g_blog
        g_blog = Baseset.get_or_insert(u'default')
        base_values['g_blog'] = g_blog
        #
        return generate(request,'tip.html',{'tip':u'Has been successfully operating.'})
    else:
        return generate(request,'tip.html',{'tip':u'You do not have permission to operate.'})

@login_required
def profile(request):
    email = str(request.user)
    try:name = email.split('@')[0]
    except:name = email
    obj = Profile.get_or_insert(u"key_%s"%email, displayname = name ,email = email)    
    if request.method == 'POST':
        if email != obj.email:
            return generate(request,'tip.html',{'tip':u'You do not have permission to operate.'})
        form = ProfileForm(request.POST)
        if form.is_valid():
            old_ads_l = obj.art_left
            old_ads_r = obj.art_right
            
            cd = form.cleaned_data
            displayname = del_html(cd['displayname'])
            if not displayname:
                displayname = name
            if displayname != name:
                #check exist
                displayname_exist = Profile.all().filter('displayname =', displayname).get()
                if displayname_exist and obj != displayname_exist:
                    return generate(request,'tip.html',{'tip':"displayname exist."})
            aboutme = del_html(cd['aboutme'])
            signtext = del_html(cd['signtext'])
            #art_left = cd['art_left']
            #art_right = cd['art_right']            
            obj.displayname = displayname
            obj.web = cd['web']
            obj.aboutme = aboutme
            obj.signtext = signtext
            #if old_ads_l != art_left or old_ads_r != art_right:
            #    obj.art_left = art_left
            #    obj.art_right = art_right
            #    obj.pub_ads = False
            obj.put()
    else:
        form = ProfileForm(instance=obj)
    return generate(request,'profile.html',{'obj':obj,'form':form})

def show_profile(request,key):
    obj = Profile.get(key)
    if obj:
        form = ProfileForm(instance=obj)
        return generate(request,'show_profile.html',{'obj':obj,'form':form})
    else:
        HttpResponseRedirect("/")

def robots(request):
    current_site = get_current_site(request)
    return render_to_response(request,'robots.txt',{'current_site_domain':current_site.domain})

def getsitemapxml(request,cate_list):
    current_site = get_current_site(request)
        
    # get from mem
    sitemap = memcache.get("%s_sitemap_men_%s"%(cur_app,current_site.domain))
    #sitemap = None
    if sitemap:
        return sitemap
    #
    urls = []
    #
    loc = "http://%s"%current_site.domain
    lastmod = "%s"%(now().strftime('%Y-%m-%dT%X+00:00'))
    changefreq = 'always'
    priority = '1.0'
    urlstr = "<url>\n<loc>%s</loc>\n<lastmod>%s</lastmod>\n<changefreq>%s</changefreq>\n<priority>%s</priority>\n</url>\n"%(loc,lastmod,changefreq,priority)
    urls.append(urlstr)   
    #
    
    for cate in cate_list:
        ##get cate
        loc = u"http://%s%s" % (current_site.domain,cate.get_absolute_url())
        lastmod = "%s"%(now().strftime('%Y-%m-%dT%X+00:00'))
        changefreq = 'hourly'
        priority = '0.7'
        urlstr = "<url>\n<loc>%s</loc>\n<lastmod>%s</lastmod>\n<changefreq>%s</changefreq>\n<priority>%s</priority>\n</url>\n"%(loc,lastmod,changefreq,priority)
        urls.append(urlstr)
        ##get cate art
        cate_arts = cate.posts
        for art in cate_arts:
            if art:
                loc = u"http://%s%s" % (current_site.domain,art.get_absolute_url())
                lastmod = "%s"%(art.pub_time.strftime('%Y-%m-%dT%X+00:00'))
                changefreq = 'daily'
                priority = '0.5'
                urlstr = "<url>\n<loc>%s</loc>\n<lastmod>%s</lastmod>\n<changefreq>%s</changefreq>\n<priority>%s</priority>\n</url>\n"%(loc,lastmod,changefreq,priority)
                urls.append(urlstr)
    #####
    sitemap = ''.join(urls)
    memcache.add("%s_sitemap_men_%s"%(cur_app,current_site.domain), sitemap, 3600*3)#3h
    return sitemap

def sitemap(request):
    cate_list = get_categories()    
    xmlbody = getsitemapxml(request,cate_list)
    return render_to_response(request,'sitemap.xml',{'xml':xmlbody})

def rsslatest(request):
    current_site = get_current_site(request)
    # get from mem
    xmlbody = memcache.get("%s_rsslatest_men_%s"%(cur_app,current_site.domain))
    #sitemap = None
    if xmlbody:
        return HttpResponse(xmlbody,content_type='application/rss+xml')
    
    baseurl = "http://%s"%current_site.domain
    site_name = g_blog.title
    now_time = now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    subtitle = site_name
    feedurl = "rss.xml"
    
    xml_list = []
    xml_list.append(u'<?xml version="1.0" encoding="UTF-8"?> \n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n<atom:link href="%s%s" rel="self" type="application/rss+xml" /> \n'%( baseurl, reverse('app1.views.rsslatest')))
    xml_list.append(u' xmlns:atom="http://www.w3.org/2005/Atom"')
    head_str = u'<title>%s</title> \n<link>%s</link> \n<description>%s Latest Articles</description> \n<language>en-us</language> \n<copyright>Copyright (C) %s. All rights reserved.</copyright> \n<pubDate>%s</pubDate> \n<lastBuildDate>%s</lastBuildDate>\n<generator>%s RSS Generator</generator> \n'%(site_name,baseurl,site_name,current_site.domain,now_time,now_time,current_site.domain)
    xml_list.append(head_str)
    
    newpostlist = Entry.all().order('-pub_time').fetch(50)
    
    for art in newpostlist:
        art_time = art.pub_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
        art_url = "%s%s"%(baseurl,art.get_absolute_url())
        alltagstring = ""
        if art.tags:
            alltagstring = "Tags: "
            for eachtag in art.tags:
                alltagstring = alltagstring + '%s, ' %eachtag
        tmp_str = u'<item> \n<title> %s </title> \n<link>%s</link> \n<guid>%s</guid> \n<description><![CDATA[\n <a href="%s" target="_blank">%s</a> \n %s \n %s]]></description> \n<category>%s</category> \n<author>%s(%s)</author> \n<pubDate>%s</pubDate>  \n</item> \n'%(art.title, art_url, art_url, art_url, art.title, art.content, alltagstring, art.category.name, art.author,art.author_name, art_time)
        xml_list.append(tmp_str)
    xml_list.append(u'</channel>\n</rss>\n')
    xmlbody = ''.join(xml_list)
    memcache.add("%s_rsslatest_men_%s"%(cur_app,current_site.domain), xmlbody, 3600*3)#3h
    
    return HttpResponse(xmlbody,content_type='application/rss+xml')


def subscribe_tags(request):
    try:
        query = Keyword.all().fetch(1000)
        subs = list_subscriptions(Document) # Get all subscriptions for Documents
        taglist = []
        
        for eachtag in query:
            taglist.append(eachtag.tag)
#            logging.info("add tag %s" %eachtag.tag)
        for sub in subs:
            unsubscribe(Document, sub[1])
#            logging.info("remove subscribe %s" %sub[1])
        
        for tag in taglist:
            subscribe(Document, tag, tag)
#            logging.info("add subscribe %s" %tag)
            
        return HttpResponse(content="%d tags subscribed!" %len(taglist),content_type='text/plain')  
    except Exception, e:
        err = "Failed to update subscription, exception\n%s" % e
        logging.error(err)
        return HttpResponse(content="No Tag Subscribed! Error : %s" %err,content_type='text/plain')

def fetch(request):
    try:
        feeds = Feed.all().order('crawl_time').fetch(1)#db.GqlQuery("SELECT * FROM Feed ORDER BY crawl_time")
        if len(feeds) == 0:
            return HttpResponse(content='No Feeds!',content_type='text/plain')
        else:
            feed = feeds[0]
            result = urlfetch.fetch(feed.url)
            last_guid = feed.last_guid
            
            if result.status_code == 200:
                data = parse(result.content)
                i = 0
                if len(data.entries) > 0:
                    if data.entries[0].guid is None:
                        feed.crawl_time = datetime.datetime.now()
                        feed.put()
                        return HttpResponse(content="No GUID Error",content_type='text/plain')
                    last_guid = data.entries[0].guid['original-id']
                    logging.info("%s,,,," %data.entries[0].guid['original-id'])
    
                    for entry in data.entries:
                        if entry.guid['original-id'] == feed.last_guid:
                            break
        
                        i = i + 1
                  
                        feed_content = ""
                  
                        if 'content' in entry:
                            for c in entry.content:
                                feed_content = feed_content + c.value + "\n"
                        elif 'summary' in entry:
                            feed_content = entry.summary
                        
                        doclink = ""
                        if 'link' in entry:
                            doclink = entry.link
                        
                        
                        if len(feed_content) < 3000:
                            continue
                        
                        doc = Document(feed = feed.name, guid = entry.guid['original-id'], author = entry.author_detail.name, title = entry.title, content = feed_content, status = 1, category = feed.category,link = doclink, retries = 0)
                        doc.put()
                
                feed.crawl_time = datetime.datetime.now()
                if i > 0:
                    feed.last_guid = last_guid
                    # feed.feed_update_time = data.updated_parsed
                
                    feed.put()
                    return HttpResponse(content='%d Entries fetched.' % i,content_type='text/plain')
                    #self.response.out.write("%d entries fetched from %s" % (i, feed.url))
                else:
                    feed.put()
                    return HttpResponse(content='Fetch completed, %d new entries.'% i,content_type='text/plain')
                    #self.response.out.write("Fetch completed, no entries fetched from %s" % feed.url)
            else:
              return HttpResponse(content='Error fetching feed %s...' %feed.url,content_type='text/plain')
              #self.response.out.write("Error fetching feed %s" % feed.url)
    except Exception, e:
        return HttpResponse(content="Error fetching feed, exception: \n %s" % e,content_type='text/plain')
        #self.response.out.write("Error fetching feed, exception: \n %s" % e)


def match_tags(request):
    try:
        query = Document.all().filter('status',1).fetch(20)
        for doc in query:
            doc.status=2
            doc.put()
            match(document = doc, result_batch_size=1000)
        return HttpResponse(content="%d matched!" %len(query),content_type='text/plain')
    except Exception, e:
        err = "Unable to match %s, Exception: %s" %(doc.title, e)
        return HttpResponse(content="Error: %s!" %err,content_type='text/plain')
      
def replace_tags(request):
    try:
        current_site = get_current_site(request)
        query = Document.all().filter('status',3).fetch(20)
        for doc in query:
            taglist = doc.tags
            taglist.sort(key=lambda x:-len(x))
            tags = []
            for tag in taglist:
                replace=1
                # see if replaced 
#                for t in tags:
#                    if t.find(tag) != -1:
#                        replace = 0
#                        break
                if replace == 1:# let's replace the string
                    idx = 0
                    replacetimes = 0
                    while idx < len(doc.content):
                        idx = doc.content.lower().find(tag.lower(), idx)
                        if idx == -1: # the end
                            break
                        
                        # see if already in <a> tag
                        atag_begin = doc.content.lower().find("<a href", idx)
                        atag_end = doc.content.lower().find("</a>", idx)
            
                        if atag_end != -1 and (atag_begin == -1 or atag_begin > atag_end): # already in <a> tag, ignore
                            idx = idx + len(tag)
                            continue
                        
                        temp = '<a href="http://www.financeguider.info/tag/%s">' %tag
                        doc.content = doc.content[:idx] + temp + doc.content[idx:]
                        idx = idx + len(tag) + len(temp)
                        doc.content = doc.content[:idx] + "</a>" + doc.content[idx:]
                        replacetimes += 1
                        
                        if replacetimes >= 3:
                            break
                    
#                    tags.append(tag)
            doc.status=4
            doc.put()
        return HttpResponse(content="%d replaced!" %len(query),content_type='text/plain')
    except Exception, e:
        err = "Unable to replace %s, Exception: %s" %(doc.title, e)
        return HttpResponse(content="Error: %s!" %err,content_type='text/plain')
      

#def record_tags(request):
#    try:
#        doc = get_document(request.POST)
#        logging.info(doc)
#        document = Document.get(key(doc))
#
#        document.status = 3
#        document.retries = 0
#        
#        tags = []
#        for sub_id in request.POST.get('id'):
#            tags.append(sub_id)
#        document.tags = tags
#        document.put()
#        return HttpResponse(content="%s 's tags recorded!" %document.title,content_type='text/plain')
#    except Exception, e:
#        err = "Unable to process, Exception: %s" %e
#        logging.info("Unable to process, Exception: %s"%e )
#        return HttpResponse(content="Error: %s!" %err,content_type='text/plain')
#      

def documentarticle(request):
    tags = ''
    obj = None
    documentlist1 = Document.all().filter('status', 4).fetch(20)
    documentlist2 = Document.all().filter('status', 2).fetch(5)
    
    authorid = Entry.all().get().author
    logging.info(authorid)
    
    for eachdocument in documentlist1:
        title = eachdocument.title
        title = title.replace(u'-',u'_')
        title = title.replace(u'…',u'')
        arttitle_exist = Entry.all().filter('title =', title).get()
        if arttitle_exist:
            continue
        
        taglist = eachdocument.tags
        abstract = del_html(eachdocument.content)[:300] + " ..."
        post_now = now()
        obj = Entry(author = authorid, #request.user,
                title = title,
                abstract = abstract,
                content = eachdocument.content.replace("<p>&nbsp;</p>",""),
                slug = title.replace(" ","_"),
                commentclosed = True,
                tags = taglist,
                pub_time = post_now,
                category = eachdocument.category,
                original_author = eachdocument.author,
                original_link = eachdocument.link
                )
        obj.put()
        if obj.is_saved():
            #Category
            cat = obj.category
            if obj.key() not in cat.post_keys:
                cat.post_keys.insert(0,obj.key())
                if cat.entrycount >= 999:
                    cat.post_keys = cat.post_keys[:999]
                cat.entrycount = len(cat.post_keys)
                cat.put()
            #tags
            if obj.tags:
                for tag in obj.tags:
                    tag_obj = Tag.get_or_insert(u"key_%s"%tag,tag = tag, entrycount = 1, post_keys = [obj.key()])
                    if obj.key() not in tag_obj.post_keys:
                        tag_obj.post_keys.insert(0,obj.key())
                        if tag_obj.entrycount >= 999:
                            tag_obj.post_keys = tag_obj.post_keys[:999]
                        tag_obj.entrycount = len(tag_obj.post_keys)
                        tag_obj.put()
            #removecache
            memcache.delete("%s_rsslatest_men_%s"%(cur_app,get_current_site(request).domain))
            memcache.delete("newposts_key")
            memcache.delete("category_posts_%d"%(obj.category.key().id()))
            if obj.category.entrycount >=10:
                allpage = (obj.category.entrycount+1)/10 + 1
                for p in range(1,allpage+1):
                    memcache.delete("category_posts_%d_page_%d"%(obj.category.key().id(),p))                
            for tag in obj.tags:
                memcache.delete(u"tag_posts_key_%s"%(tag))
        eachdocument.delete()                        
    for eachdocument in documentlist2:
        title = eachdocument.title
        title = title.replace(u'-',u'_')
        title = title.replace(u'…',u'')
        arttitle_exist = Entry.all().filter('title =', title).get()
        if arttitle_exist:
            continue
        
        taglist = eachdocument.tags
        abstract = del_html(eachdocument.content)[:300] + " ..."
        post_now = now()
        obj = Entry(author = authorid, #request.user,
                title = title,
                abstract = abstract,
                content = eachdocument.content.replace("<p>&nbsp;</p>",""),
                slug = title.replace(" ","_"),
                commentclosed = True,
                tags = taglist,
                pub_time = post_now,
                category = eachdocument.category,
                original_author = eachdocument.author,
                original_link = eachdocument.link
                )
        obj.put()
        if obj.is_saved():
            #Category
            cat = obj.category
            if obj.key() not in cat.post_keys:
                cat.post_keys.insert(0,obj.key())
                if cat.entrycount >= 999:
                    cat.post_keys = cat.post_keys[:999]
                cat.entrycount = len(cat.post_keys)
                cat.put()
            #tags
            if obj.tags:
                for tag in obj.tags:
                    tag_obj = Tag.get_or_insert(u"key_%s"%tag,tag = tag, entrycount = 1, post_keys = [obj.key()])
                    if obj.key() not in tag_obj.post_keys:
                        tag_obj.post_keys.insert(0,obj.key())
                        if tag_obj.entrycount >= 999:
                            tag_obj.post_keys = tag_obj.post_keys[:999]
                        tag_obj.entrycount = len(tag_obj.post_keys)
                        tag_obj.put()
            #removecache
            memcache.delete("%s_rsslatest_men_%s"%(cur_app,get_current_site(request).domain))
            memcache.delete("newposts_key")
            memcache.delete("category_posts_%d"%(obj.category.key().id()))
            if obj.category.entrycount >=10:
                allpage = (obj.category.entrycount+1)/10 + 1
                for p in range(1,allpage+1):
                    memcache.delete("category_posts_%d_page_%d"%(obj.category.key().id(),p))                
            for tag in obj.tags:
                memcache.delete(u"tag_posts_key_%s"%(tag))
        eachdocument.delete()                        
    return HttpResponse(content="%d Entry converted!" %(len(documentlist1)+len(documentlist2)),content_type='text/plain')
      
def generate_daily(request):
    try:
        query = Entry.all().order('-pub_time').fetch(30)
        doc_list = []
        for doc in query:
            docstring = u'<p><a href="%s" target="_blank">%s</a> \n %s \n\n<p>' %(doc.get_absolute_url(),doc.title,doc.abstract)
            doc_list.append(docstring)
        doclistxml = "".join(doc_list)
        doctitle = "Personal Finance Guide Update: " + now().strftime('%d %b %Y %H:%M:%S')
        obj = DailyRSS(title = doctitle, content = doclistxml)
        obj.put()
        logging.info(doclistxml)
        return HttpResponse(content="generated!",content_type='text/plain')
    except Exception, e:
        err = "Unable to generate %s, Exception: %s" %(doc.title, e)
        return HttpResponse(content="Error: %s!" %err,content_type='text/plain')
    

def rssdaily(request):
    current_site = get_current_site(request)
    # get from mem
    xmlbody = memcache.get("%s_rssdaily_men_%s"%(cur_app,current_site.domain))
    #sitemap = None
    if xmlbody:
        return HttpResponse(xmlbody,content_type='application/rss+xml')
    
    baseurl = "http://www.financeguider.info/"
    site_name = g_blog.title
    now_time = now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    subtitle = site_name
    feedurl = "rssdaily.xml"
    
    xml_list = []
    xml_list.append(u'<?xml version="1.0" encoding="UTF-8"?> \n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n<atom:link href="%s%s" rel="self" type="application/rss+xml" /> \n'%( baseurl, reverse('app1.views.rssdaily')))
    xml_list.append(u' xmlns:atom="http://www.w3.org/2005/Atom"')
    head_str = u'<title>%s</title> \n<link>%s</link> \n<description>%s Latest Articles</description> \n<language>en-us</language> \n<copyright>Copyright (C) %s. All rights reserved.</copyright> \n<pubDate>%s</pubDate> \n<lastBuildDate>%s</lastBuildDate>\n<generator>%s RSS Generator</generator> \n'%(site_name,baseurl,site_name,current_site.domain,now_time,now_time,current_site.domain)
    xml_list.append(head_str)
    
    newpostlist = DailyRSS.all().order('-updated_time').fetch(10)
    #query = db.GqlQuery("SELECT * FROM Entry where pub_time < %s ORDER BY crawl_time" %)
    
    for art in newpostlist:
        art_time = art.updated_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
#        art_url = "%s%s"%(baseurl,art.get_absolute_url())
#        alltagstring = ""
#        if art.tags:
#            alltagstring = "Tags: "
#            for eachtag in art.tags:
#                alltagstring = alltagstring + '%s, ' %eachtag
        tmp_str = u'<item> \n<title> %s </title> \n<link>%s</link> \n<guid>%s</guid> \n<description><![CDATA[\n %s \n]]></description> \n<pubDate>%s</pubDate>  \n</item> \n'%(art.title, baseurl, art.title, art.content, art_time)
        xml_list.append(tmp_str)
    xml_list.append(u'</channel>\n</rss>\n')
    xmlbody = ''.join(xml_list)
    memcache.add("%s_rssdaily_men_%s"%(cur_app,current_site.domain), xmlbody, 3600*3)#3h
    
    return HttpResponse(xmlbody,content_type='application/rss+xml')


def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
    