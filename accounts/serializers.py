"""
User Serializers for TaskFlow AI
================================================================================
Laravel equivalent: app/Http/Resources/UserResource.php
                   + app/Http/Requests/RegisterRequest.php
================================================================================

Serializers in DRF = Resources + Form Requests combined in Laravel
- They handle both INPUT validation and OUTPUT formatting
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for reading user data.
    
    Laravel equivalent:
    class UserResource extends JsonResource {
        public function toArray($request) {
            return [
                'id' => $this->id,
                'email' => $this->email,
                ...
            ];
        }
    }
    """
    full_name = serializers.ReadOnlyField()  # Computed property from model
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'avatar',
            'bio',
            'timezone',
            'date_joined',
        ]
        # Laravel equivalent: $hidden in model
        read_only_fields = ['id', 'email', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Laravel equivalent:
    class RegisterRequest extends FormRequest {
        public function rules() {
            return [
                'email' => 'required|email|unique:users',
                'password' => 'required|min:8|confirmed',
            ];
        }
    }
    """
    # password field with write_only (won't be returned in response)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],  # Django's built-in password validation
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
        ]
    
    def validate(self, attrs):
        """
        Validate that passwords match.
        Laravel equivalent: Custom validation in FormRequest
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Passwords don't match."
            })
        return attrs
    
    def create(self, validated_data):
        """
        Create user with hashed password.
        
        Laravel equivalent:
        User::create([
            'password' => Hash::make($request->password),
            ...
        ]);
        """
        # Remove password_confirm as it's not a model field
        validated_data.pop('password_confirm')
        
        # create_user() automatically hashes the password
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    
    Laravel equivalent: UpdateProfileRequest
    """
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'bio',
            'timezone',
            'avatar',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change.
    
    Laravel equivalent: ChangePasswordRequest
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "New passwords don't match."
            })
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
