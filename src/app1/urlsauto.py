# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

rootpatterns = patterns('',
    (r'', include('app1.urls')),
)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()