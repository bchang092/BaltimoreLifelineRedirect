from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import ServiceInquiry


@override_settings(ALLOWED_HOSTS=['testserver'], EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   EMAIL_HOST_USER='sender@example.com', EMAIL_HOST_PASSWORD='test-password',
                   DEFAULT_FROM_EMAIL='sender@example.com', LUMA_INQUIRY_EMAIL='baltimorelifeline@gmail.com')
class LumaReachTests(TestCase):
    def setUp(self):
        self.payload = {'name': 'Test Person', 'email': 'person@example.com', 'organization': 'Test team',
                        'service': 'scraping', 'message': 'We need a structured directory of public resources.'}

    def test_brand_and_external_chapter_links(self):
        self.assertEqual(reverse('luma_home'), '/')
        home = self.client.get('/')
        self.assertContains(home, 'LumaReach')
        self.assertNotContains(home, 'Luma Reach')
        self.assertContains(home, 'href="https://www.baltimorelifeline.site/"')
        self.assertContains(home, 'href="/about/"')
        self.assertEqual(self.client.get('/baltimore/').status_code, 404)

    def test_inquiry_saved_privately_and_email_sent_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/', self.payload)
        self.assertRedirects(response, '/#contact', fetch_redirect_response=False)
        inquiry = ServiceInquiry.objects.get()
        self.assertFalse(inquiry.contacted)
        self.assertEqual(inquiry.email, self.payload['email'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['baltimorelifeline@gmail.com'])
        self.assertEqual(mail.outbox[0].reply_to, [self.payload['email']])
        self.assertContains(self.client.get('/'), 'Your inquiry has been received')
        self.assertNotContains(self.client.get('/'), 'Your inquiry has been received')
        self.assertEqual(ServiceInquiry.objects.count(), 1)
        self.assertNotContains(Client().get('/'), self.payload['message'])
        self.assertEqual(self.client.get('/admin/inquiries/serviceinquiry/').status_code, 302)

    def test_invalid_fields_and_honeypot_do_not_save(self):
        for changes in ({'email': 'bad'}, {'name': ' '}, {'service': 'unknown'},
                        {'message': 'x' * 5001}, {'website': 'bot.example'}):
            with self.subTest(changes=list(changes)):
                response = self.client.post('/', self.payload | changes)
                self.assertEqual(response.status_code, 400)
                self.assertContains(response, 'Please check your inquiry', status_code=400)
        self.assertFalse(ServiceInquiry.objects.exists())

    def test_rate_limit_and_csrf(self):
        for _ in range(5):
            self.client.post('/', self.payload | {'email': 'bad'})
        response = self.client.post('/', self.payload)
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response['Retry-After']), 0)
        self.assertFalse(ServiceInquiry.objects.exists())
        self.assertEqual(Client(enforce_csrf_checks=True).post('/', self.payload).status_code, 403)

    @patch('inquiries.views.EmailMessage.send', side_effect=SMTPException('unavailable'))
    def test_email_failure_does_not_lose_inquiry(self, send):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/', self.payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ServiceInquiry.objects.count(), 1)
        send.assert_called_once()

    @override_settings(EMAIL_HOST_PASSWORD='')
    def test_saving_without_smtp(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/', self.payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ServiceInquiry.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)
