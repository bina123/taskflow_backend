"""
Custom Permissions for TaskFlow AI
================================================================================
Laravel equivalent: app/Policies/ProjectPolicy.php
================================================================================
"""
from rest_framework import permissions
from .models import ProjectMember

class IsProjectMember(permissions.BasePermission):
    """
    Check user is member of the project
    """
    message = "You are not a memeber of this project"
    
    def has_object_permission(self,request, view, obj):
        if obj.owner == request.user:
            return True
        
        return obj.memberships.filter(user=request.user).exists()
    
class IsProjectAdmin(permissions.BasePermission):
    """
    Check if user is owner or admin of the project
    """
    message = "You must be project owner or admin"
    
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True
        
        # Check if user is admin member
        return obj.memberships.filter(
            user = request.user,
            role = ProjectMember.Role.ADMIN
        ).exists()
        
class IsTaskProjectMember(permissions.BasePermission):
    """
    Check if user is a member of the task's project.
    
    Used for Task views.
    """
    message = "You are not a member of this task's project."
    def has_object_permission(self, request, view, obj):
        project = obj.project
        
        if project.owner == request.user:
            return True
        
        return project.memberships.filter(user=request.user).exists()
    
class CanAssignTask(permissions.BasePermission):
    """
    Check if user can assign task (must be owner, admin or assignee)
    """
    message = "You don't have permission to assign this task."
    
    def has_object_permission(self, request, view, obj):
        project = obj.project
        
        if project.owner == request.user:
            return True
        
        is_admin = project.memberships.filter(
            user=request.user,
            role = ProjectMember.Role.ADMIN
        )
        
        if is_admin:
            return True
        
        assignee_id = request.data.get('assignee')
        if assignee_id is None or int(assignee_id) == request.user.id:
            return True
        
        return False
    
class CanChangeStatus(permissions.BasePermission):
    """
    Check if user is assignee or admin/owner 
    """
    message = "You don't have permission to change status of this task."
    
    def has_object_permission(self, request, view, obj):
        project = obj.project
        
        if project.owner == request.user:
            return True
        
        is_admin = project.memberships.filter(
            user = request.user,
            role= ProjectMember.Role.ADMIN
        ).exists()
        
        if is_admin:
            return True
            
        if obj.assignee == request.user:
            return True

        return False