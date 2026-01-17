"""
Project Models for TaskFlow AI
================================================================================
Laravel equivalent: app/Models/Project.php + app/Models/ProjectMember.php
================================================================================
"""

from django.db import models
from django.conf import settings


class Project(models.Model):
    """
    Project model - container for tasks.
    
    Laravel equivalent:
    class Project extends Model {
        protected $fillable = ['name', 'description', 'status', 'color'];
        
        public function owner() {
            return $this->belongsTo(User::class, 'owner_id');
        }
        
        public function members() {
            return $this->belongsToMany(User::class, 'project_members');
        }
        
        public function tasks() {
            return $this->hasMany(Task::class);
        }
    }
    """
    
    class Status(models.TextChoices):
        """
        Project status choices.
        Laravel equivalent: const STATUS_ACTIVE = 'active'; (or Enum in PHP 8.1+)
        """
        ACTIVE = 'active', 'Active'
        ARCHIVED = 'archived', 'Archived'
        COMPLETED = 'completed', 'Completed'
    
    # Basic fields
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    
    # Owner relationship
    # Laravel: $table->foreignId('owner_id')->constrained('users')->onDelete('cascade');
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects'  # Access via: user.owned_projects.all()
    )
    
    # Status with choices
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    # Project color for UI
    color = models.CharField(max_length=7, default='#6366f1')  # Hex color
    
    # Timestamps
    # Laravel: $table->timestamps();
    created_at = models.DateTimeField(auto_now_add=True)  # Set on create
    updated_at = models.DateTimeField(auto_now=True)      # Set on every save
    
    class Meta:
        db_table = 'projects'
        ordering = ['-updated_at']
        # Laravel equivalent: Unique constraint
        # $table->unique(['owner_id', 'name']);
    
    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    """
    Project membership (many-to-many through model).
    
    Laravel equivalent:
    // In migration:
    Schema::create('project_members', function (Blueprint $table) {
        $table->foreignId('project_id')->constrained()->onDelete('cascade');
        $table->foreignId('user_id')->constrained()->onDelete('cascade');
        $table->enum('role', ['admin', 'member', 'viewer']);
        $table->timestamps();
        $table->unique(['project_id', 'user_id']);
    });
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
        VIEWER = 'viewer', 'Viewer'
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships'
    )
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_members'
        # Ensure user can only be member once per project
        unique_together = ['project', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.project.name} ({self.role})"
