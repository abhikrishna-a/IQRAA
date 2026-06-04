from rest_framework import serializers

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    internship_title = serializers.CharField(source='internship.title', read_only=True)

    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['student', 'status', 'applied_at', 'updated_at']

    def validate_resume(self, value):
        if value:
            if not value.name.endswith('.pdf'):
                raise serializers.ValidationError('Only PDF files are allowed')
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError('File size must be under 2MB')
        return value


class StatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status']
