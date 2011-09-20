import os
import datetime

from app1.models import *
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.dist import use_library
from google.appengine.dist import use_library

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
use_library('django', '1.1')

class MainPageHandler(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    template_values = { }
    path = os.path.join(os.path.dirname(__file__), 'templates/default.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    self.response.headers['Content-Type'] = 'text/html'
    try:
      name = self.request.get('name')
      url = self.request.get('url')

      feed = Feed(name = name, url = url)
      feed.put()

      template_values = { 'name': name }
      path = os.path.join(os.path.dirname(__file__), 'templates/success.html')
      self.response.out.write(template.render(path, template_values))
    except Exception, e:
      template_values = { }
      path = os.path.join(os.path.dirname(__file__), 'templates/error.html')
      self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication([('/', MainPageHandler)], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()