"""
Services for TaskFlow AI
================================================================================
Business logic separated from views (clean architecture)
================================================================================
"""

from .models import Activity

class ActivityService:
    """
     Service to log activities.
    
    Usage:
        ActivityService.log_task_created(user, task)
        ActivityService.log_status_change(user, task, old_status, new_status)
    """
    
    @staticmethod
    def log(user, project, action, description, task=None, details=None):
        """Base method to create activity log."""
        return Activity.objects.create(
            user=user,
            project=project,
            action=action,
            task=task,
            description=description,
            details=details or {}
        )
        
    @staticmethod
    def log_task_created(user, task):
        return ActivityService.log(
            user=user,
            project=task.project,
            action=Activity.ActionType.TASK_CREATED,
            task=task,
            description=f'created task "{task.title}"'
        )
        
    @staticmethod
    def log_task_updated(user,task, changes):
        return ActivityService.log(
            user=user,
            project=task.project,
            action=Activity.ActionType.TASK_UPDATED,
            task=task,
            description=f'updated task "{task.title}"',
            details={'changes': changes}
        )
        
    @staticmethod
    def log_task_deleted(user, project, task_title):
        return ActivityService.log(
            user=user,
            project=project,
            action=Activity.ActionType.TASK_DELETED,
            description=f'Deleted task "{task_title}"'
        )
        
    @staticmethod
    def log_status_changes(user, task, old_status, new_status):
        return ActivityService.log(
            user=user,
            project=task.project,
            action=Activity.ActionType.TASK_STATUS_CHANGED,
            task=task,
            description=f'Changed "{task.title}" from {old_status} to {new_status}',
            details={'old_status': old_status, 'new_status': new_status}
        )
        
    @staticmethod
    def log_task_assigned(user, task, assignee):
        return ActivityService.log(
            user=user,
            project=task.project,
            task=task,
            action=Activity.ActionType.TASK_ASSIGNED,
            description=f'Assigned "{task.title}" to {assignee.email}',
            details= {'assignee_id': assignee.id, 'assignee_email': assignee.email}
        )
        
    @staticmethod
    def log_task_unassigned(user, task):
        return ActivityService.log(
            user=user,
            project=task.project,
            action=Activity.ActionType.TASK_UNASSIGNED,
            task=task,
            description=f'Unassigned "{task.title}"'   
        )
        
    @staticmethod
    def log_comment_added(user, comment):
        return ActivityService.log(
            user=user,
            project=comment.task.project,
            action=Activity.ActionType.COMMENT_ADDED,
            task=comment.task,
            description=f'commented on "{comment.task.title}"'
        )
        
    @staticmethod
    def log_label_added(user, task, label):
        return ActivityService.log(
            user=user,
            project=task.project,
            task=task,
            action=Activity.ActionType.LABEL_CREATED,
            description=f'added label {label} to "{task.title}" '
        )
        
    @staticmethod
    def log_label_removed(user, task, label):
        return ActivityService.log(
            user=user,
            project=task.project,
            task=task,
            action=Activity.ActionType.LABEL_REMOVED,
            description=f"removed label {label} from {task.title}"
        )
        
    @staticmethod
    def log_memebr_joined(user, project, member):
        return ActivityService.log(
            user=user,
            project=project,
            action=Activity.ActionType.MEMBER_JOINED,
            description=f'{member.email} joined the project'
        )