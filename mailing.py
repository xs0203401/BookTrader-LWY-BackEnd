
"""
Decorator to indicate that this is a cron method and applies request.headers check
Reference: https://stackoverflow.com/questions/14193816/google-app-engine-security-of-cron-jobs

"""
# from google.appengine.api import app_identity
from google.appengine.api import mail
from main import *
import webapp2


def cron_method(handler):
    def check_if_cron(self, *args, **kwargs):
        if self.request.headers.get('X-AppEngine-Cron') is None:
            self.error(403)
        else:
            return handler(self, *args, **kwargs)
    return check_if_cron

def send_subscription_mail(sender_address, receiver_address, report_title, report_url_key):
# [START send_mail]
	mail.send_mail(sender=sender_address,
	               to=receiver_address,
	               subject="Your account has been approved",
	               body="""Dear {0}:

Your report {1}({2}) was successfully submitted. Don't forget to check it 

Please let us know if you have any questions.

Book Trader Team
""".format(receiver_address, report_title, report_url_key))
# [END send_mail]


class MailingService(webapp2.RequestHandler):
	
	# Decorator for cron check
	# @cron_method
	def get(self):
		SENDER = "postman@guestbookyaohuangliu.appspotmail.com"
		authors = Author.query()
		for author in authors:
			receiver_address = author.email
			reports = Report.query(Report.author==author)
			for r in reports:
				self.response.write()


		