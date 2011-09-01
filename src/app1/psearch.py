import datetime
import logging

from app1.models import Document,Tag
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api.prospective_search import *

class ProspectiveSearchHandler(webapp.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'text/plain'
    
    try:
      document = get_document(self.request)
      document.status = 3
      document.retries = 0
      
      tags = []
      
      for sub_id in self.request.get_all('id'):
        tags.append(sub_id)
      
      document.tags = tags
      
      document.put()
      
      msg = "Document %s successfully processed. Tags" % document.title
      self.response.out.write(msg)
      
    except Exception, e:
      err = "Unable to process, Exception: %s" % e
      self.response.out.write(err)
      

application = webapp.WSGIApplication([('/_ah/prospective_search', ProspectiveSearchHandler)], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
