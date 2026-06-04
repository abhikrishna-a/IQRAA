from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Application
from .serializers import ApplicationSerializer, StatusUpdateSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def application_list(request):
    if request.method == 'POST':
        if request.user.role != 'student':
            return Response({'error': 'Only students can apply'}, status=status.HTTP_403_FORBIDDEN)

        internship_id = request.data.get('internship')
        if Application.objects.filter(student=request.user, internship_id=internship_id).exists():
            return Response({'error': 'Duplicate application — you have already applied for this internship'}, status=status.HTTP_409_CONFLICT)

        serializer = ApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(student=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    user = request.user
    if user.role == 'student':
        applications = Application.objects.filter(student=user)
    elif user.role == 'company':
        applications = Application.objects.filter(internship__company__user=user)
    else:
        applications = Application.objects.all()

    serializer = ApplicationSerializer(applications, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_detail(request, pk):
    try:
        application = Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    if user.role == 'student' and application.student != user:
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    if user.role == 'company' and application.internship.company.user != user:
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ApplicationSerializer(application)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def application_update_status(request, pk):
    try:
        application = Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role != 'company' or application.internship.company.user != request.user:
        return Response({'error': 'Only the internship owner can update status'}, status=status.HTTP_403_FORBIDDEN)

    serializer = StatusUpdateSerializer(application, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(ApplicationSerializer(application).data)
