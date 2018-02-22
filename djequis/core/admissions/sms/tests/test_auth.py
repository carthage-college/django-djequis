from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group

from djtools.utils.logging import seperator

from djzbar.utils.informix import get_session


class CoreViewsTestCase(TestCase):

    def setUp(self):

        self.username = settings.TEST_USERNAME
        self.email = settings.TEST_EMAIL
        self.password = settings.TEST_PASSWORD
        self.user = User.objects.create_user(
            self.username, self.email, self.password
        )

        # add to student accounts group
        ag = Group.objects.create(name=settings.ADDMISSIONS_SMS_GROUP)
        ag.user_set.add(self.user)
        # cred dict
        self.credentials = {
            'username': self.username,
            'password': self.password
        }

    def test_auth(self):
        print "\n"
        print "Test Auth"
        seperator()
        earl = reverse('sms_send')
        print earl
        # get SMS send page
        response = self.client.get(earl)
        self.assertEqual(response.status_code, 302)
        # redirect to sign in page
        print "redirect to sign in at {}".format(response['location'])

        # attempt to sign in with client login method
        login = self.client.login(
            username=self.username, password=self.password
        )
        self.assertTrue(login)
        response = self.client.get(earl)
        self.assertEqual(response.status_code, 200)
        print "Auth Success"
