import io
import json
import os
from datetime import datetime

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.authentication.models import User, Role
from apps.internships.models import Company, Internship
from apps.internships.views import internship_list, RATE_LIMIT


class InternshipPaginationTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='company', email='c@t.com', password='pass', role=Role.COMPANY
        )
        self.company = Company.objects.create(user=self.user, name='Test Corp')
        for i in range(25):
            Internship.objects.create(
                company=self.company, title='Intern {}'.format(i), description='desc'
            )

    def test_pagination_defaults(self):
        req = self.factory.get('/api/internships/')
        resp = internship_list(req)
        data = resp.data
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['count'], 25)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 10)
        self.assertEqual(len(data['results']), 10)

    def test_pagination_custom_page_and_limit(self):
        req = self.factory.get('/api/internships/?page=2&limit=5')
        resp = internship_list(req)
        data = resp.data
        self.assertEqual(data['page'], 2)
        self.assertEqual(data['limit'], 5)
        self.assertEqual(len(data['results']), 5)
        self.assertEqual(data['results'][0]['title'], 'Intern 5')

    def test_rate_limit_block(self):
        key = '127.0.0.1'
        RATE_LIMIT[key] = [datetime.now().timestamp()] * 100
        req = self.factory.get('/api/internships/', REMOTE_ADDR=key)
        resp = internship_list(req)
        self.assertEqual(resp.status_code, 429)
        RATE_LIMIT.pop(key, None)
