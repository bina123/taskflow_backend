"""
User Views for TaskFlow AI
================================================================================
Laravel equivalent: app/Http/Controllers/AuthController.php
                   + app/Http/Controllers/UserController.php
================================================================================

In DRF, views handle HTTP requests just like Laravel controllers.
- APIView = basic view class (like a controller method)
- generics.* = pre-built views with common functionality
- viewsets.* = full CRUD controllers (like resource controllers)
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    
    POST /api/auth/register/
    
    Laravel equivalent:
    public function register(RegisterRequest $request) {
        $user = User::create([...]);
        return response()->json($user, 201);
    }
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]  # No auth required
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return user data (without password)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user's profile.
    
    GET /api/auth/me/      - Get profile
    PATCH /api/auth/me/    - Update profile
    
    Laravel equivalent:
    public function me(Request $request) {
        return $request->user();
    }
    
    public function update(UpdateProfileRequest $request) {
        $request->user()->update($request->validated());
        return $request->user();
    }
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Return the current authenticated user.
        Laravel equivalent: $request->user() or auth()->user()
        """
        return self.request.user
    
    def get_serializer_class(self):
        """Use different serializer for updates."""
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


class ChangePasswordView(APIView):
    """
    Change user's password.
    
    POST /api/auth/change-password/
    
    Laravel equivalent:
    public function changePassword(ChangePasswordRequest $request) {
        $request->user()->update([
            'password' => Hash::make($request->new_password)
        ]);
        return response()->json(['message' => 'Password changed']);
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Update password
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


# =============================================================================
# LEARNING NOTES FOR LARAVEL DEVELOPERS:
# =============================================================================
#
# View Types Comparison:
# ----------------------
# Laravel                          | Django REST Framework
# ---------------------------------|--------------------------------
# Controller method                | APIView with get(), post() methods
# Resource Controller              | ViewSet
# Single action controller         | generics.* views
#
# Common Generic Views:
# --------------------
# - generics.ListAPIView        = index()
# - generics.CreateAPIView      = store()
# - generics.RetrieveAPIView    = show()
# - generics.UpdateAPIView      = update()
# - generics.DestroyAPIView     = destroy()
# - generics.ListCreateAPIView  = index() + store()
# - generics.RetrieveUpdateDestroyAPIView = show() + update() + destroy()
#
# Permissions (like Laravel middleware):
# -------------------------------------
# - permissions.AllowAny         = No middleware
# - permissions.IsAuthenticated  = auth middleware
# - permissions.IsAdminUser      = admin middleware
# - Custom permissions           = Custom middleware/gates
#
# Response:
# ---------
# Laravel: return response()->json($data, 200);
# Django:  return Response(data, status=status.HTTP_200_OK)
# =============================================================================
