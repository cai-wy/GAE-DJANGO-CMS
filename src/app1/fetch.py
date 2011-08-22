import datetime
import os

from app1.models import Feed,Document
from google.appengine.api import urlfetch
from app1.feedparser import *
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from app1.html2text import html2text
from google.appengine.dist import use_library
from google.appengine.ext import db
from google.appengine.ext.db import Model as DBModel

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
use_library('django', '1.1')

class FetchHandler(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    
    try:
      query = Feed.order('crawl_time')#db.GqlQuery("SELECT * FROM Feed ORDER BY crawl_time")
      feeds = query.fetch(1)
      
      if feeds is None:
          self.response.out.write("No feeds!")
      else:
          feed = feeds[0]
    
          result = urlfetch.fetch(feed.url)
          last_guid = feed.last_guid
    
          if result.status_code == 200:
            data = parse(result.content)
            i = 0
            if len(data.entries) > 0:
              last_guid = data.entries[0].guid
    
            for entry in data.entries:
              if entry.guid == feed.last_guid:
                break
    
              i = i + 1
              
              feed_content = ""
              
              if 'content' in entry:
                for c in entry.content:
                  feed_content = feed_content + c.value + "\n"
              elif 'summary' in entry:
                feed_content = entry.summary
              
              doc = Document(feed = feed.name, guid = entry.guid, author = entry.author_detail.name, title = entry.title, content = html2text(feed_content, feed.url), status = 1)
              doc.put()
    
            if i > 0:
              feed.last_guid = last_guid
              # feed.feed_update_time = data.updated_parsed
              feed.crawl_time = datetime.datetime.now()
              feed.put()
              self.response.out.write("%d entries fetched from %s" % (i, feed.url))
            else:
              self.response.out.write("Fetch completed, no entries fetched from %s" % feed.url)
              
          else:
            self.response.out.write("Error fetching feed %s" % feed.url)
    except Exception, e:
      self.response.out.write("Error fetching feed, exception: \n %s" % e)
    
    
      
application = webapp.WSGIApplication([('/fetch', FetchHandler)], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()


