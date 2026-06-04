import io
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.authentication.models import User, Role
from apps.internships.models import Company, Internship
from apps.applications.models import Application
from apps.applications.views import application_list, application_update_status


class ResumeUploadTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.student = User.objects.create_user(
            username='stu', email='s@t.com', password='pass', role=Role.STUDENT
        )
        company_user = User.objects.create_user(
            username='comp', email='c@t.com', password='pass', role=Role.COMPANY
        )
        self.company = Company.objects.create(user=company_user, name='Corp')
        self.internship = Internship.objects.create(company=self.company, title='Test', description='x')

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


class StatusUpdateTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.student = User.objects.create_user(
            username='stu', email='s@t.com', password='pass', role=Role.STUDENT
        )
        self.company_user = User.objects.create_user(
            username='comp', email='c@t.com', password='pass', role=Role.COMPANY
        )
        company = Company.objects.create(user=self.company_user, name='Corp')
        internship = Internship.objects.create(company=company, title='Test', description='x')
        self.application = Application.objects.create(student=self.student, internship=internship)

    def test_invalid_status_returns_400_not_500(self):
        req = self.factory.patch('/api/applications/{}/status/'.format(self.application.id),
                                 {'status': 'invalid_status'}, format='json')
        force_authenticate(req, user=self.company_user)
        resp = application_update_status(req, pk=self.application.id)
        self.assertEqual(resp.status_code, 400)

    def test_student_cannot_update_status(self):
        req = self.factory.patch('/api/applications/{}/status/'.format(self.application.id),
                                 {'status': 'accepted'}, format='json')
        force_authenticate(req, user=self.student)
        resp = application_update_status(req, pk=self.application.id)
        self.assertEqual(resp.status_code, 403)

    def test_nonexistent_application_returns_404(self):
        req = self.factory.patch('/api/applications/999/status/', {'status': 'accepted'}, format='json')
        force_authenticate(req, user=self.company_user)
        resp = application_update_status(req, pk=999)
        self.assertEqual(resp.status_code, 404)
