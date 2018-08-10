# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
import webapp2
import jinja2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates/WIP"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_THEME = "default"

def theme_key(theme_name=DEFAULT_THEME):
    return ndb.Key('Theme', theme_name)

def user_check(self):
    user = users.get_current_user()
    if user:
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
    else:
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
    return user, url, url_linktext


class Author(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

class Report(ndb.Model):
    author = ndb.StructuredProperty(Author)
    theme = ndb.StringProperty(indexed=False)
    title = ndb.StringProperty(indexed=False)
    tag = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    image = ndb.BlobKeyProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class ViewPhotoHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, photo_key):
        if not blobstore.get(photo_key):
            self.error(404)
        else:
            self.send_blob(photo_key)

class MainPage(webapp2.RequestHandler):

    def get(self):

        user, url, url_linktext = user_check(self)

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }


        
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class CreateReport(blobstore_handlers.BlobstoreUploadHandler):

    def get(self):

        user, url, url_linktext = user_check(self)
        
        # Image Upload Url
        upload_url = blobstore.create_upload_url('/create_report')

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'upload_action': upload_url,
        }


        
        template = JINJA_ENVIRONMENT.get_template('create_report.html')
        self.response.write(template.render(template_values))

    def post(self):
        
        user, url, url_linktext = user_check(self)

        # Saving image
        upload = self.get_uploads()[0]

        report_theme = self.request.get('theme', DEFAULT_THEME)
        report = Report(parent=theme_key(report_theme))
        report.theme = self.request.get('theme')
        report.title = self.request.get('title')
        report.tag = self.request.get('tags')
        report.description = self.request.get('description')
        report.image = upload.key()
        
        report.put()

        # self.response.write('''<html><body>You wrote:</br>"''')
        # self.response.write(report.theme+"</br>")
        # self.response.write(report.title+"</br>")
        # self.response.write(report.tag+"</br>")
        # self.response.write(report.description+"</br>")
        # self.response.write('''<body><html>''')
        # self.response.write('success!')

        query_params = {'report_theme': report_theme}
        self.redirect('/reports?' + urllib.urlencode(query_params))


class ThemesPage(webapp2.RequestHandler):

    def get(self):
                
        # guestbook_name = self.request.get('guestbook_name',
        #                                   DEFAULT_GUESTBOOK_NAME)
        # greetings_query = Greeting.query(
        #     ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        # greetings = greetings_query.fetch(10)

        template = JINJA_ENVIRONMENT.get_template('themes.html')
        self.response.write(template.render(template_values))


class Reports(webapp2.RequestHandler):

    def get(self):

        user, url, url_linktext = user_check(self)

        # guestbook_name = self.request.get('guestbook_name',
        #                                   DEFAULT_GUESTBOOK_NAME)
        # greetings_query = Greeting.query(
        #     ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        # greetings = greetings_query.fetch(10)


        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('reports.html')
        self.response.write(template.render(template_values))


class ManageThemes(webapp2.RequestHandler):

    def get(self):


        template = JINJA_ENVIRONMENT.get_template('manage.html')
        self.response.write(template.render(template_values))




# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/themes', ThemesPage),
    ('/reports', Reports),
    ('/manage_themes', ManageThemes),
    ('/create_report', CreateReport),
    ('/view_photo/([^/]+)?', ViewPhotoHandler),
], debug=True)
# [END app]