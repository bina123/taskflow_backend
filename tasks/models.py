"""
Task Models for TaskFlow AI
================================================================================
Laravel equivalent: app/Models/Task.php + app/Models/Comment.php
================================================================================
"""

from django.db import models
from django.conf import settings


class Task(models.Model):
    """
    Task model - the main work item.
    
    Laravel equivalent:
    class Task extends Model {
        protected $fillable = ['title', 'description', 'status', 'priority', ...];
        
        protected $casts = [
            'due_date' => 'date',
        ];
        
        public function project() { return $this->belongsTo(Project::class); }
        public function assignee() { return $this->belongsTo(User::class); }
        public function comments() { return $this->hasMany(Comment::class); }
    }
    """
    
    class Status(models.TextChoices):
        """Task status for Kanban board columns."""
        TODO = 'todo', 'To Do'
        IN_PROGRESS = 'in_progress', 'In Progress'
        REVIEW = 'review', 'Review'
        DONE = 'done', 'Done'
    
    class Priority(models.TextChoices):
        """Task priority levels."""
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'
    
    # Basic fields
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    
    # Relationships
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    
    # Creator of the task
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    
    # Assigned user (nullable - task can be unassigned)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    
    # Status and priority
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    
    # Due date (optional)
    due_date = models.DateField(null=True, blank=True)
    
    # Position for ordering in Kanban columns
    position = models.PositiveIntegerField(default=0)
    
    # ==========================================================================
    # AI-Generated Fields (what makes TaskFlow AI special!)
    # ==========================================================================
    
    # AI-estimated time to complete (in hours)
    ai_time_estimate = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='AI-estimated hours to complete'
    )
    
    # AI-suggested priority
    ai_suggested_priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        ordering = ['position', '-created_at']
    
    def __str__(self):
        return self.title


class Comment(models.Model):
    """
    Comment model for task discussions.
    
    Laravel equivalent:
    class Comment extends Model {
        protected $fillable = ['content'];
        
        public function task() { return $this->belongsTo(Task::class); }
        public function user() { return $this->belongsTo(User::class); }
    }
    """
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_comments'
    )
    
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.task.title}"


class Label(models.Model):
    """
    Label/Tag model for categorizing tasks.
    
    Laravel equivalent: Many-to-many with pivot table
    """
    
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6366f1')
    
    # Labels belong to a project
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='labels'
    )
    
    # Many-to-many with tasks
    tasks = models.ManyToManyField(
        Task,
        related_name='labels',
        blank=True
    )
    
    class Meta:
        db_table = 'labels'
        unique_together = ['project', 'name']
    
    def __str__(self):
        return self.name
    
class Activity(models.Model):
    """
    Activity logs for tracking all changes
    """
    class ActionType(models.TextChoices):
        TASK_CREATED= 'task_created', 'Task Created'
        TASK_UPDATED = 'task_updated', 'Task Updated'
        TASK_DELETED = 'task_deleted', 'Task Deleted'
        TASK_STATUS_CHANGED = 'task_status_changed', "Task Status Changed"
        TASK_ASSIGNED = 'task_assigned', 'Task Assigned'
        TASK_UNASSIGNED = 'task_unassigned', 'Task Unassigned' 
        
        #Comment actions
        COMMENT_ADDED = 'comment_added', 'Comment Added'
        COMMENT_DELETED = 'comment_deleted', 'Comment Deleted'
        
        #Label Actions
        LABEL_CREATED = 'label_created', 'Label Created'
        LABEL_REMOVED = 'label_removed', 'Label Removed'
        
        #Project actions
        MEMBER_JOINED = 'member_joined', 'Member Joined'
        MEMBER_LEFT = 'member_left', 'Member Left'
        PROJECT_UPDATED = 'project_updated', 'Project Updated'
        
    #Who performed the action
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities'
    )
    
    # Which project
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='activities'
    )

    #Action Type
    action = models.CharField(
        max_length=50,
        choices= ActionType.choices
    )

    # Optional: Related task
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    
    details = models.JSONField(default=dict, blank=True)
    
    description = models.CharField(max_length=500)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activities'
        ordering = ['-created_at']
        verbose_name_plural = 'Activities'
        
    def __str__(self):
        return f"{self.user} {self.action} - {self.created_at}"