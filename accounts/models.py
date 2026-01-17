"""
User Model for TaskFlow AI
================================================================================
Laravel equivalent: app/Models/User.php
================================================================================

Key differences from Laravel:
- Django uses AbstractUser for extending the default User
- Fields are defined using Django's model fields (not $fillable/$guarded)
- related_name is like Laravel's relationship method names
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    AbstractUser already includes:
    - username, email, password
    - first_name, last_name
    - is_active, is_staff, is_superuser
    - date_joined, last_login
    
    Laravel equivalent fields:
    - $fillable = ['name', 'email', 'password']
    - $hidden = ['password', 'remember_token']
    """
    
    # Make email required and unique (optional in default Django)
    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.',
        }
    )
    
    # Profile picture
    # Laravel equivalent: $table->string('avatar')->nullable();
    avatar = models.ImageField(
        upload_to='avatars/',  # Files stored in MEDIA_ROOT/avatars/
        blank=True,
        null=True
    )
    
    # Short bio
    # Laravel equivalent: $table->text('bio')->nullable();
    bio = models.TextField(
        max_length=500,
        blank=True,
        default=''
    )
    
    # User's timezone preference
    # Laravel equivalent: $table->string('timezone')->default('UTC');
    timezone = models.CharField(
        max_length=50,
        default='UTC'
    )
    
    # Use email for authentication instead of username
    # Laravel equivalent: public function username() { return 'email'; }
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'  # Laravel equivalent: protected $table = 'users';
        ordering = ['-date_joined']
    
    def __str__(self):
        """String representation of the user."""
        return self.email
    
    @property
    def full_name(self):
        """
        Get user's full name.
        Laravel equivalent: public function getFullNameAttribute()
        """
        return f"{self.first_name} {self.last_name}".strip() or self.username
