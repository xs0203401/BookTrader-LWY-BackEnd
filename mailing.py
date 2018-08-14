"""
Decorator to indicate that this is a cron method and applies request.headers check
Reference: https://stackoverflow.com/questions/14193816/google-app-engine-security-of-cron-jobs

"""
# from google.appengine.api import app_identity
from google.appengine.api import mail
import webapp2


def cron_method(handler):
    def check_if_cron(self, *args, **kwargs):
        if self.request.headers.get('X-AppEngine-Cron') is None:
            self.error(403)
        else:
            return handler(self, *args, **kwargs)
    return check_if_cron

def send_approved_mail(sender_address):
# [START send_mail]
	mail.send_mail(sender=sender_address,
	               to="Henry Johnson <yaohuang.liu@utexas.edu>",
	               subject="Your account has been approved",
	               body="""Dear Henry:

Your example.com account has been approved.  You can now visit
http://www.example.com/ and sign in using your Google Account to
access new features.

Please let us know if you have any questions.

The example.com Team
""")
# [END send_mail]


class MailingService(webapp2.RequestHandler):
	
	# Decorator for cron check
	@cron_method
	def get(self):
		sender_address = "postman@guestbookyaohuangliu.appspotmail.com"
		# sender_address = "xs020340@gmail.com"
		send_approved_mail(sender_address)
		