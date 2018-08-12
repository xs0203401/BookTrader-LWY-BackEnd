# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import search
import webapp2
import jinja2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates/WIP"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# [END imports]

DEFAULT_THEME = "T1"

def user_check(self):
    user = users.get_current_user()
    if user:
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
    else:
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
    return user, url, url_linktext


def theme_key(theme_name=DEFAULT_THEME):
    return ndb.Key('theme_name', theme_name)

class Theme(ndb.Model):
    theme_name = ndb.StringProperty()

def THEME_INITIALIZE():
    t1=Theme()
    t1.theme_name="Information Systems"
    t1.put()
    t2=Theme()
    t2.theme_name="Business"
    t2.put()
    t3=Theme()
    t3.theme_name="Statistics"
    t3.put()

class Author(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

class Report(ndb.Model):
    author = ndb.StructuredProperty(Author)
    title = ndb.StringProperty(indexed=False)
    # tag = ndb.StringProperty(indexed=False, repeated=True)
    tag = ndb.StringProperty(indexed=True)
    theme = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    image = ndb.BlobKeyProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

    def _post_put_hook(self, future):
        doc = search.Document(doc_id=self.key.urlsafe(), 
            fields=[search.TextField(name='tags', value=self.tag)])
        search.Index('tags').put(doc)

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
        
        theme_items = Theme.query()
        
        # Image Upload Url
        upload_url = blobstore.create_upload_url('/create_report')

        report_theme = self.request.get('theme')

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'upload_action': upload_url,
            'theme_items': theme_items,
            'report_theme': report_theme,
        }
        
        template = JINJA_ENVIRONMENT.get_template('create_report.html')
        self.response.write(template.render(template_values))

    def post(self):
        
        user, url, url_linktext = user_check(self)

        # Saving image
        upload = self.get_uploads()[0]

        # Create Entity
        report_theme = self.request.get('theme', DEFAULT_THEME)
        report = Report(parent=theme_key(report_theme))
        # Checking Author
        if users.get_current_user():
            report.author = Author(
                identity=users.get_current_user().user_id(),
                email=users.get_current_user().email())
        else:
            report.author = Author(
                identity="Anonymous",
                email="unknown@unknown.com")
        report.theme = report_theme
        report.title = self.request.get('title')
        report_tags = self.request.get('tags')
        report.tag = ",".join(set([i.strip() for i in report_tags.split(',')]))
        # report.tag = report_tags
        report.description = self.request.get('description')
        report.image = upload.key()

        report.put()

        query_params = {'report_theme': report_theme, 'page_num': 1}
        self.redirect('/reports?' + urllib.urlencode(query_params))


class ThemesPage(webapp2.RequestHandler):

    def get(self):
                
        # guestbook_name = self.request.get('guestbook_name',
        #                                   DEFAULT_GUESTBOOK_NAME)
        # greetings_query = Greeting.query(
        #     ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        # greetings = greetings_query.fetch(10)
        user, url, url_linktext = user_check(self)

        # pass "0" when testing to initialize first 3 Themes
        if self.request.get('I')=="0":
            THEME_INITIALIZE()

        theme_items = Theme.query()

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'theme_items': theme_items,
        }

        template = JINJA_ENVIRONMENT.get_template('themes.html')
        self.response.write(template.render(template_values))


class ReportsPage(webapp2.RequestHandler):

    def get(self):

        user, url, url_linktext = user_check(self)

        # guestbook_name = self.request.get('guestbook_name',
        #                                   DEFAULT_GUESTBOOK_NAME)
        # greetings_query = Greeting.query(
        #     ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        # greetings = greetings_query.fetch(10)

        report_theme=self.request.get('report_theme')
        # if theme is not specified go to Themes page
        if report_theme=='':
            self.redirect('/themes')
            return

        page_num = int(self.request.get('page_num', 1))

        reports_query = Report.query(
            ancestor=theme_key(report_theme)).order(-Report.date)
        report_items = reports_query.fetch(5, offset=5*(page_num-1))

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'page_num': page_num,
            'report_theme': report_theme,
            'reports': report_items,
        }

        template = JINJA_ENVIRONMENT.get_template('reports.html')
        self.response.write(template.render(template_values))


class ManageThemes(webapp2.RequestHandler):

    def get(self):
        user, url, url_linktext = user_check(self)
        
        theme_items = Theme.query()

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'theme_items': theme_items,
        }


        template = JINJA_ENVIRONMENT.get_template('manage.html')
        self.response.write(template.render(template_values))

class ReportsSearch(webapp2.RequestHandler):

    def get(self):
        user, url, url_linktext = user_check(self)

        query_string = self.request.get('queryString')
        page_num = int(self.request.get('page_num', 1))

        if query_string=='':
            reports_query = Report.query()
            report_items = reports_query.fetch(5, offset=5*(page_num-1))
            # self.response.write(report_items)
        else:
            options = search.QueryOptions(limit=10)
            query = search.Query(query_string=query_string, options=options)
            results = search.Index('tags').search(query)

            report_items = []
            for doc in results:
                doc_ID = doc.doc_id
                # self.response.write("<p>id</p>")
                # self.response.write(doc_ID)

                # self.response.write("<p>report by id</p>")
                report_key = ndb.Key(urlsafe=doc_ID)
                item = report_key.get()
                # self.response.write(item)

                report_items.append(item)


        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'page_num': page_num,
            'query_string': query_string,
            'reports': report_items,
        }

        template = JINJA_ENVIRONMENT.get_template('reports_search.html')
        self.response.write(template.render(template_values))




# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/themes', ThemesPage),
    ('/reports', ReportsPage),
    ('/s', ReportsSearch),
    ('/manage_themes', ManageThemes),
    ('/create_report', CreateReport),
    ('/view_photo/([^/]+)?', ViewPhotoHandler),
], debug=True)
# [END app]