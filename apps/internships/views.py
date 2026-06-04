from datetime import datetime

from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Company, Internship
from .serializers import CompanySerializer, InternshipSerializer
from .permissions import IsCompanyUser, IsOwner

RATE_LIMIT = {}
RATE_LIMIT_MAX = 100
RATE_LIMIT_WINDOW = 900


def check_rate_limit(request):
    try:
        key = request.META.get('REMOTE_ADDR', 'unknown')
        now = datetime.now().timestamp()
        window_start = now - RATE_LIMIT_WINDOW
        if key not in RATE_LIMIT:
            RATE_LIMIT[key] = []
        RATE_LIMIT[key] = [t for t in RATE_LIMIT[key] if t > window_start]
        if len(RATE_LIMIT[key]) >= RATE_LIMIT_MAX:
            return False
        RATE_LIMIT[key].append(now)
        return True
    except Exception:
        return True


# ── Companies ──

@api_view(['GET', 'POST'])
def company_list(request):
    if request.method == 'GET':
        try:
            companies = Company.objects.all()
            serializer = CompanySerializer(companies, many=True)
            return Response(serializer.data)
        except Exception:
            return Response({'error': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    serializer = CompanySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        serializer.save(user=request.user)
    except IntegrityError:
        return Response({'error': 'A company profile already exists for this user'}, status=status.HTTP_409_CONFLICT)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def company_detail(request, pk):
    try:
        company = Company.objects.get(pk=pk)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CompanySerializer(company)
        return Response(serializer.data)

    if not request.user.is_authenticated or request.user != company.user:
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = CompanySerializer(company, data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        serializer.save()
    except IntegrityError:
        return Response({'error': 'Cannot update company -- data conflict'}, status=status.HTTP_409_CONFLICT)
    return Response(serializer.data)

    if request.method == 'DELETE':
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = CompanySerializer(company, data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        serializer.save()
    except IntegrityError:
        return Response({'error': 'Cannot update company — data conflict'}, status=status.HTTP_409_CONFLICT)
    return Response(serializer.data)


# ── Internships ──

@api_view(['GET', 'POST'])
def internship_list(request):
    if request.method == 'POST':
        for p in [IsAuthenticated(), IsCompanyUser()]:
            if not p.has_permission(request, None):
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = InternshipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save(company=request.user.company)
        except IntegrityError:
            return Response({'error': 'Internship data conflict'}, status=status.HTTP_409_CONFLICT)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    if not check_rate_limit(request):
        return Response({'error': 'Rate limit exceeded. Try again later.'}, status=429)

    try:
        qs = Internship.objects.select_related('company').all()
    except Exception:
        return Response({'error': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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

    try:
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        if page < 1 or limit < 1:
            raise ValueError
    except (ValueError, TypeError):
        return Response({'error': 'Invalid pagination parameters'}, status=status.HTTP_400_BAD_REQUEST)

    total = qs.count()
    start = (page - 1) * limit
    end = start + limit
    qs = qs[start:end]

    serializer = InternshipSerializer(qs, many=True)
    return Response({
        'count': total,
        'page': page,
        'limit': limit,
        'total_pages': (total + limit - 1) // limit,
        'results': serializer.data,
    })


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def internship_detail(request, pk):
    try:
        internship = Internship.objects.select_related('company').get(pk=pk)
    except Internship.DoesNotExist:
        return Response({'error': 'Internship not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = InternshipSerializer(internship)
        return Response(serializer.data)

    if not IsOwner().has_object_permission(request, None, internship):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        internship.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    partial = request.method == 'PATCH'
    serializer = InternshipSerializer(internship, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    try:
        serializer.save()
    except IntegrityError:
        return Response({'error': 'Internship data conflict'}, status=status.HTTP_409_CONFLICT)
    return Response(serializer.data)
