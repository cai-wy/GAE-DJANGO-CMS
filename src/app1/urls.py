# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('app1.views',
    (r'^$', 'index'),
    (r'^sitemap.xml$', 'sitemap'),
    (r'^rss.xml$', 'rsslatest'),
    (r'^index.xml$', 'rsslatest'),
    (r'^category/(?P<keyid>.+)/(?P<name>.+)$', 'category_article'),
    (r'^tag/(?P<tag>.+)$', 'tag_article'),
    #
    (r'^add_article$', 'add_article'),
    (r'^article/(?P<keyid>.+)/(?P<title>.+)$', 'show_article'),
    (r'^a/(?P<keyid>.+)$', 'show_article_short'),
    (r'^edit_article/(?P<key>.+)$', 'edit_article'),
    (r'^del_article/(?P<key>.+)$', 'del_article'),
    (r'^lastcomments$', 'lastcomments'),
    (r'^del_comment/(?P<key>.+)$', 'del_comment'),
    (r'^emptymem$', 'emptymem'),
    (r'^profile$', 'profile'),
    (r'^profile/(?P<key>.+)$', 'show_profile'),
    (r'^myarticles$', 'myarticles'),
)
