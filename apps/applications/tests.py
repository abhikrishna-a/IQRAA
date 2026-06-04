import io
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.authentication.models import User, Role
from apps.internships.models import Company, Internship
from apps.applications.views import application_list


class ResumeUploadTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.student = User.objects.create_user(
            username='stu', email='s@t.com', password='pass', role=Role.STUDENT
        )
        company_user = User.objects.create_user(
            username='comp', email='c@t.com', password='pass', role=Role.COMPANY
        )
        company = Company.objects.create(user=company_user, name='Corp')
        self.internship = Internship.objects.create(company=company, title='Test', description='x')

    def test_resume_pdf_accepted(self):
        pdf = SimpleUploadedFile('resume.pdf', b'%PDF-1.4 fake pdf content', content_type='application/pdf')
        req = self.factory.post('/api/applications/', {
            'internship': self.internship.id,
            'resume': pdf,
        }, format='multipart')
        force_authenticate(req, user=self.student)
        resp = application_list(req)
        self.assertEqual(resp.status_code, 201)
        self.assertIn('resume', resp.data)

    def test_resume_non_pdf_rejected(self):
        txt = SimpleUploadedFile('resume.txt', b'not a pdf', content_type='text/plain')
        req = self.factory.post('/api/applications/', {
            'internship': self.internship.id,
            'resume': txt,
        }, format='multipart')
        force_authenticate(req, user=self.student)
        resp = application_list(req)
        self.assertEqual(resp.status_code, 400)
