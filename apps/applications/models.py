from django.conf import settings
from django.db import models


class ApplicationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    REJECTED = 'rejected', 'Rejected'


class Application(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    internship = models.ForeignKey('internships.Internship', on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True)
    status = models.CharField(max_length=10, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'internship')

    def __str__(self):
        return f'{self.student.username} → {self.internship.title}'
