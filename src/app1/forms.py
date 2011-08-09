# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, ugettext as __
from app1.models import Category,Entry,Comment,Profile,Links
import re

class CategoryForm(forms.ModelForm):
    def cleaned_data(self):
        memcache.delete("key_all_categories")
        return self.cleaned_data
    
    class Meta:
        exclude = ['entrycount','post_keys']
        model = Category

class EntryForm(forms.ModelForm):
    title = forms.CharField(required = True,widget=forms.widgets.Input(attrs={'style':"width:500px;padding:4px;"}), max_length=50, label=_(u'Title'))
    content = forms.CharField(required = True,widget=forms.widgets.Textarea(attrs={'style':"width:600px;height:400px;",'rows': 22,'cols': 75,'class':'tinymce'}), max_length=10000, label=_(u'Content'))
    abstract = forms.CharField(required = False,widget=forms.widgets.Textarea(attrs={'style':"width:540px;height:60px;border:1px solid #999999;"}), max_length=300, label=_(u'Abstract'),help_text=_(u'Max length 300s'))
    slug = forms.CharField(required = False,widget=forms.widgets.Input(attrs={'style':"width:500px;padding:4px;"}), max_length=60, label=_(u'slug'))
        
    class Meta:
        exclude = ['author','tags','prev_key','next_key','pub_time','commentcount','comment_keys']
        model = Entry

class CommentForm(forms.ModelForm):
    name = forms.CharField(required = True,widget=forms.widgets.Input(attrs={'class':"text"}), max_length=20, label=_(u'Name'))
    message = forms.CharField(required = True,widget=forms.widgets.Textarea(attrs={'style':"width:500px;height:100px;"}), max_length=300, label=_(u'Message'),help_text=_(u'Max length 300s'))
    web = forms.URLField(required = False,widget=forms.widgets.Input(attrs={'class':"text"}), max_length=150 , label=_(u'Web'), help_text=_(u'ex: http://www.google.com'))
    
    def clean(self):
        message = self.cleaned_data.get('message','')
        if message:
            message = message.replace("<script","< script")
            message = message.replace("</script>","< /script>")
            p = re.compile( '[\n\r]{2,}')
            message = p.sub( '\n', message)             
            message = message.replace("\n","<br/>")
        self.cleaned_data['message'] = message
        return self.cleaned_data
        
    class Meta:
        exclude = ['entry','date','email','gravatar']
        model = Comment

class ProfileForm(forms.ModelForm):
    displayname = forms.CharField(required = True,widget=forms.widgets.Input(attrs={'class':"text"}), max_length=15, label=_(u'Display name'))
    web = forms.URLField(required = False,widget=forms.widgets.Input(attrs={'class':"text"}), max_length=150 , label=_(u'Web'), help_text=_(u'ex: http://www.google.com'))
    aboutme = forms.CharField(required = False,widget=forms.widgets.Textarea(attrs={'style':"width:300px;height:100px;"}), max_length=300, label=_(u'About me'),help_text=_(u'Max length 300s'))
    signtext = forms.CharField(required = False,widget=forms.widgets.Input(attrs={'class':"text"}), max_length=50, label=_(u'Sign text'),help_text=_(u'Max length 50s'))
    #art_left = forms.CharField(required = False,widget=forms.widgets.Textarea(attrs={'style':"width:300px;height:100px;"}), max_length=300, label=_(u'Article top_left ads'),help_text=_(u'Put your Google AdSense to your articles top_left, Formats : 300 x 250 is required and Image Only is best.'))
    #art_right = forms.CharField(required = False,widget=forms.widgets.Textarea(attrs={'style':"width:300px;height:100px;"}), max_length=300, label=_(u'Article top_right ads'),help_text=_(u'Put your Google AdSense to your articles top_right, Formats : 300 x 250 is required and Text Only is best.'))
    
    class Meta:
        exclude = ['author','email','pub_ads','art_left','art_right','gravatar']
        model = Profile

class LinksForm(forms.ModelForm):
    def cleaned_data(self):
        memcache.delete("links_key")
        return self.cleaned_data
    
    class Meta:
        model = Links

