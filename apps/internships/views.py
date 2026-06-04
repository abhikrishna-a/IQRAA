from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Company, Internship
from .serializers import CompanySerializer, InternshipSerializer
from .permissions import IsCompanyUser, IsOwner

# ── Companies ──

@api_view(['GET', 'POST'])
def company_list(request):
    if request.method == 'GET':
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)

    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    serializer = CompanySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def company_detail(request, pk):
    try:
        company = Company.objects.get(pk=pk)
    except Company.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CompanySerializer(company)
        return Response(serializer.data)

    serializer = CompanySerializer(company, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


# ── Internships ──

@api_view(['GET', 'POST'])
def internship_list(request):
    if request.method == 'POST':
        permission_classes = [IsAuthenticated, IsCompanyUser]
        for p in permission_classes:
            if not p().has_permission(request, None):
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = InternshipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=request.user.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    qs = Internship.objects.all()
    search = request.query_params.get('search')
    if search:
        qs = qs.filter(
            title__icontains=search
        ) | qs.filter(
            description__icontains=search
        ) | qs.filter(
            requirements__icontains=search
        )
    status_param = request.query_params.get('status')
    if status_param:
        qs = qs.filter(status=status_param)
    location = request.query_params.get('location')
    if location:
        qs = qs.filter(location__icontains=location)
    company_id = request.query_params.get('company_id')
    if company_id:
        qs = qs.filter(company_id=company_id)
    serializer = InternshipSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def internship_detail(request, pk):
    try:
        internship = Internship.objects.get(pk=pk)
    except Internship.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = InternshipSerializer(internship)
        return Response(serializer.data)

    if request.method == 'DELETE':
        owner_check = IsOwner()
        if not owner_check.has_object_permission(request, None, internship):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        internship.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    owner_check = IsOwner()
    if not owner_check.has_object_permission(request, None, internship):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    partial = request.method == 'PATCH'
    serializer = InternshipSerializer(internship, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
