# app/views.py
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Department, Employee, Room, Booking
from .serializers import DepartmentSerializer, EmployeeSerializer, RoomSerializer, BookingSerializer
import jwt
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from datetime import timedelta, timezone
from datetime import datetime
from rest_framework.decorators import action


exp = datetime.now(timezone.utc) + timedelta(hours=1)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer



class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]



class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Booking validation error:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["patch"], url_path="update-status")
    def update_status(self, request, pk=None):
        booking = self.get_object()
        new_status = request.data.get("status")

        if new_status not in ["pending", "approved", "rejected", "cancelled"]:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = new_status
        booking.save()
        return Response({"message": "Status updated", "status": booking.status})
    
    @action(detail=False, methods=["get"], url_path="by-employee/(?P<employee_id>[^/.]+)")
    def by_employee(self, request, employee_id=None):
        """Get all bookings for a specific employee"""
        bookings = Booking.objects.filter(employee_id=employee_id).select_related('room', 'employee')
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)



class EmployeeLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        
        try:
            employee = Employee.objects.get(email=email)
        except Employee.DoesNotExist:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if employee.password != password:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(employee) 
        
        return Response({
            "employee_id": employee.id,
            "email": employee.email,
            "role": employee.role,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })
