# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import search
from google.appengine.api import mail
import webapp2
import jinja2
import json


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# [END imports]

# admin users list:
ADMIN_USERS = ['xs020340@gmail.com','difu.wu@utexas.edu','yeshuai95@utexas.edu']



def user_check(self):
    user = users.get_current_user()
    if user:
        login_url = users.create_logout_url(self.request.uri)
        login_url_linktext = 'Logout'
        email=users.get_current_user().email()
    else:
        login_url = users.create_login_url(self.request.uri)
        login_url_linktext = 'Login'
        email="none"
    return user, email, login_url, login_url_linktext


def theme_key(theme_name):
    return ndb.Key('theme_name', theme_name)


# [Models]
class Theme(ndb.Model):
    theme_name = ndb.StringProperty()
    theme_description = ndb.StringProperty()
    theme_image = ndb.BlobKeyProperty(indexed=False)


class Author(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class SubMail(ndb.Model):
    email = ndb.StringProperty(indexed=True)
    theme_name = ndb.StringProperty(indexed=False, repeated=True)


class Report(ndb.Model):
    author = ndb.StructuredProperty(Author)
    title = ndb.StringProperty(indexed=False)
    tag = ndb.StringProperty(indexed=True, repeated=True)
    theme = ndb.StringProperty(indexed=False)
    geo_point = ndb.GeoPtProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    image = ndb.BlobKeyProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
    url_safe = ndb.StringProperty(indexed=False)

    def _post_put_hook(self, future):
        doc = search.Document(doc_id=self.key.urlsafe(), 
            fields=[search.TextField(name='tags', value=', '.join(self.tag))])
        search.Index('tags').put(doc)


# Initilizing temp tag set for auto completion
REPORT_TAGS_SET = set()
reports_query = Report.query().order(-Report.date)  
report_items = reports_query.fetch(20)
for item in report_items:
    for t in item.tag:
        REPORT_TAGS_SET.add(t)


class ViewPhotoHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, photo_key):
        if not blobstore.get(photo_key):
            self.error(404)
        else:
            self.send_blob(photo_key)


class MainPage(webapp2.RequestHandler):

    def get(self):

        user, email, login_url, login_url_linktext = user_check(self)


        # report_items = Report.query().fetch(10)

        template_values = {
            'user': user,
            'u_nick': email,
            'url': login_url,
            'url_linktext': login_url_linktext,
            'report_items': report_items,
        }
        
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class CreateReport(blobstore_handlers.BlobstoreUploadHandler):

    def get(self):

        user, email, login_url, login_url_linktext = user_check(self)
        
        theme_items = Theme.query()
        
        # Image Upload Url
        upload_url = blobstore.create_upload_url('/create_report')

        report_theme = self.request.get('theme')

        template_values = {
            'user': user,
            'u_nick': email,
            'url': login_url,
            'url_linktext': login_url_linktext,
            'upload_action': upload_url,
            'theme_items': theme_items,
            'report_theme': report_theme,
            'REPORT_TAGS_SET': REPORT_TAGS_SET,
        }
        
        template = JINJA_ENVIRONMENT.get_template('create_report.html')
        self.response.write(template.render(template_values))

    def post(self):
        
        user, email, login_url, login_url_linktext = user_check(self)

        # Saving image
        upload = self.get_uploads()[0]

        # Create Entity
        report_theme = self.request.get('theme')
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
        rep_lat = float(self.request.get('lat'))
        rep_lng = float(self.request.get('lng'))
        report.geo_point = ndb.GeoPt(rep_lat, rep_lng)
        report_tags = set([ t.title() for t in [i.strip() for i in report_tags.split(',')] if t!=''])
        report.tag = [t for t in report_tags]
        for t in report_tags:
            REPORT_TAGS_SET.add(t)

        report.description = self.request.get('description')
        report.image = upload.key()

        # store and save url_safe
        key = report.put()
        url_key = key.urlsafe()
        temp = key.get()
        temp.url_safe = url_key
        temp.put()

        query_params = {'report_theme': report_theme, 'page_num': 1}
        self.redirect('/reports?' + urllib.urlencode(query_params))


class ThemesPage(webapp2.RequestHandler):

    def get(self):
                
        user, email, login_url, login_url_linktext = user_check(self)


        if email in ADMIN_USERS:
            manage_themes_TF = 1
        else:
            manage_themes_TF = 0

        theme_items = Theme.query()

        template_values = {
            'user': user,
            'u_nick': email,
            'url': login_url,
            'url_linktext': login_url_linktext,
            'manage_themes_TF': manage_themes_TF,
            'theme_items': theme_items,
        }

        template = JINJA_ENVIRONMENT.get_template('themes.html')
        self.response.write(template.render(template_values))


class M_Themes(webapp2.RequestHandler):

    def get(self):

        theme_items = Theme.query()
        reports_value = []
        for item in theme_items:
            reports_value.append({
                'name': item.theme_name,
                'description': item.theme_description,
                'image': str(item.theme_image)
                })

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(reports_value))


class ReportsPage(webapp2.RequestHandler):

    def get(self):

        user, email, login_url, login_url_linktext = user_check(self)

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
            'u_nick': email,
            'url': login_url,
            'url_linktext': login_url_linktext,
            'page_num': page_num,
            'report_theme': report_theme,
            'reports': report_items,
        }

        template = JINJA_ENVIRONMENT.get_template('reports.html')
        self.response.write(template.render(template_values))


class M_Reports(webapp2.RequestHandler):

    def get(self):

        report_theme=self.request.get('theme')
        report_items = Report.query(ancestor=theme_key(report_theme)).order(-Report.date).fetch(10)

        reports_value = []
        for item in report_items:
            reports_value.append({
                'author_email': item.author.email,
                'title': item.title,
                'tag': item.tag,
                'theme': item.theme,
                'geo_lat': item.geo_point.lat,
                'geo_lng': item.geo_point.lon,
                'description': item.description,
                'image': '/view_photo/'+str(item.image),
                'url':item.url_safe,
                'date': str(item.date),
            })

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(reports_value))


class ReportsSearch(webapp2.RequestHandler):

    def get(self):
        user, email, login_url, login_url_linktext = user_check(self)

        query_string = self.request.get('queryString')
        page_num = int(self.request.get('page_num', 1))

        if query_string=='':
            reports_query = Report.query()
            report_items = reports_query.fetch(5, offset=5*(page_num-1))
        else:
            options = search.QueryOptions(limit=10)
            query = search.Query(query_string=query_string, options=options)
            results = search.Index('tags').search(query)

            report_items = []
            for doc in results:
                doc_ID = doc.doc_id
                report_key = ndb.Key(urlsafe=doc_ID)
                item = report_key.get()
                if item!=None:
                    report_items.append(item)


        template_values = {
            'user': user,
            'u_nick': email,
            'url': login_url,
            'url_linktext': login_url_linktext,
            'page_num': page_num,
            'query_string': query_string,
            'reports': report_items,
            'REPORT_TAGS_SET': REPORT_TAGS_SET,
        }

        template = JINJA_ENVIRONMENT.get_template('reports_search.html')
        self.response.write(template.render(template_values))


class ManageThemes(blobstore_handlers.BlobstoreUploadHandler):

    def get(self):
        user, email, login_url, login_url_linktext = user_check(self)
        # Admin check:
        if email not in ADMIN_USERS:
            self.redirect('/themes')
            return

        upload_url = blobstore.create_upload_url('/manage_themes')

        theme_items = Theme.query()

        template_values = {
            'user': user,
            'u_nick': email,
            # admin role required; Logout/login not avalible
            'theme_items': theme_items,
            'upload_action': upload_url,
        }

        template = JINJA_ENVIRONMENT.get_template('manage.html')
        self.response.write(template.render(template_values))

    def post(self):
        # Check theme name
        theme_name = self.request.get('theme')
        # Check if it's delete operation
        if self.request.get('deleteCheck')=='on':
            if theme_name=='new': 
                self.redirect('/manage_themes')
                return
            theme_key = Theme.query(Theme.theme_name==theme_name).fetch(keys_only=True)
            theme = theme_key[0].delete()
        else:
            # Saving cover image
            upload = self.get_uploads()[0]

            if theme_name=='new':
                # new, create new theme entity
                theme = Theme()
                theme.theme_name = self.request.get('name')
                theme.theme_description = self.request.get('description')
                theme.theme_image = upload.key()
                theme.put()
            else:
                # edit theme
                theme_key = Theme.query(Theme.theme_name==theme_name).fetch(keys_only=True)
                theme = theme_key[0].get()
                theme.theme_name = self.request.get('name')
                theme.theme_description = self.request.get('description')
                theme.theme_image = upload.key()
                theme.put()
        self.redirect('/manage_themes')


class ViewReport(webapp2.RequestHandler):

    def get(self):
        user, email, login_url, login_url_linktext = user_check(self)

        url_safe = self.request.get('key')

        report_key = ndb.Key(urlsafe=url_safe)

        this_report = report_key.get()

        template_values = {
            'user': user,
            'u_nick': email,
            'url': login_url,
            'url_linktext': login_url_linktext,
            'report': this_report,
        }

        template = JINJA_ENVIRONMENT.get_template('view_report.html')
        self.response.write(template.render(template_values))


class M_ViewReport(webapp2.RequestHandler):

    def get(self):
        url_safe = self.request.get('key')

        report_key = ndb.Key(urlsafe=url_safe)

        this_report = report_key.get()

        this_report_value = {
            'author_email': this_report.author.email,
            'title': this_report.title,
            'tag': this_report.tag,
            'theme': this_report.theme,
            'geo_lat': this_report.geo_point.lat,
            'geo_lng': this_report.geo_point.lon,
            'description': this_report.description,
            'image': '/view_photo/'+str(this_report.image),
            'date': str(this_report.date),
        }

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(this_report_value))


class DeleteReport(webapp2.RequestHandler):

    def get(self):
        url_safe = self.request.get('key')
        report_key = ndb.Key(urlsafe=url_safe)
        report_key.delete()
        self.redirect('/themes')


class MyAccount(webapp2.RequestHandler):

    def get(self):
        user, email, login_url, login_url_linktext = user_check(self)
        sub = SubMail.query(SubMail.email==email)
        num = sub.count()
        if num!=0:
            this_sub = sub.fetch(1)[0]
        else:
            this_sub = ''

        theme_items = Theme.query()

        template_values = {
            'user': user,
            'u_nick': email,
            'url': login_url,
            'url_linktext': login_url_linktext,
            'num': num,
            'sub': this_sub,
            'theme_items': theme_items,
        }

        template = JINJA_ENVIRONMENT.get_template('my_acct.html')
        self.response.write(template.render(template_values))

    def post(self):
        theme_items = Theme.query()
        # sub_email = self.request.get('address')
        user, email, login_url, login_url_linktext = user_check(self)
        sub_email = email
        sub_theme_name = [i_theme.theme_name 
            for i_theme in theme_items 
            if self.request.get(i_theme.theme_name)=='on']
        sub = SubMail.query(SubMail.email==sub_email)
        num = sub.count()
        if num!=0:
            this_sub = sub.fetch(keys_only=True)[0]
            this_sub = this_sub.get()
            this_sub.theme_name = sub_theme_name
        else:
            this_sub = SubMail(email=sub_email,theme_name=sub_theme_name)
        this_sub.put()
        self.redirect('/my')


def cron_method(handler):
    # Reference: http://work.newmusic.pp.ua/questions/14193816/google-app-engine-security-of-cron-jobs
    def check_if_cron(self, *args, **kwargs):
        if self.request.headers.get('X-AppEngine-Cron') is None:
            self.error(403)
        else:
            return handler(self, *args, **kwargs)
    return check_if_cron

def send_subscription_mail(sender_address, receiver_address, report_name):
# [START send_mail]
    mail.send_mail(sender=sender_address,
                   to=receiver_address,
                   subject="Don't forget to check your subscribed theme~!",
                   body="""Dear {0}:

View your subscription of {1}: https://guestbookyaohuangliu.appspot.com/reports?report_theme={1}

Please let us know if you have any questions.

Book Trader Team
""".format(receiver_address, report_name))
# [END send_mail]

class MailingService(webapp2.RequestHandler):
    
    # Decorator for cron check
    @cron_method
    def get(self):
        SENDER = "postman@guestbookyaohuangliu.appspotmail.com"
        mail_sub_s = SubMail.query().fetch()
        for mail_sub in mail_sub_s:
            for theme_name in mail_sub.theme_name:
                send_subscription_mail(SENDER, mail_sub.email, theme_name)




# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/themes', ThemesPage),
    ('/m/themes', M_Themes),
    ('/reports', ReportsPage),
    ('/m/reports', M_Reports),
    ('/view_report', ViewReport),
    ('/m/view_report', M_ViewReport),
    ('/s', ReportsSearch),
    ('/manage_themes', ManageThemes),
    ('/my', MyAccount),
    ('/del', DeleteReport),
    ('/mailing', MailingService),
    ('/create_report', CreateReport),
    ('/view_photo/([^/]+)?', ViewPhotoHandler),
], debug=True)
# [END app]