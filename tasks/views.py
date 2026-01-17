"""
Task Views for TaskFlow AI
================================================================================
Laravel equivalent: app/Http/Controllers/TaskController.php
================================================================================
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F

from projects.permissions import IsTaskProjectMember, CanAssignTask, IsProjectAdmin, CanChangeStatus
from projects.models import ProjectMember, Project

from .models import Task, Comment, Label
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskReorderSerializer,
    TaskWithCommentsSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    LabelCreateSerializer,
    LabelUpdateSerializer,
    LabelSerializer
)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations.
    
    Laravel equivalent:
    class TaskController extends Controller {
        public function index(Request $request) { ... }
        public function store(StoreTaskRequest $request) { ... }
        public function show(Task $task) { ... }
        public function update(UpdateTaskRequest $request, Task $task) { ... }
        public function destroy(Task $task) { ... }
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Task.objects.all()
    
    def get_permissions(self):
        """
        Different permissions for different actions.
        """
        
        if self.action in ['update','partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsTaskProjectMember()]
        elif self.action == 'assign':
            return [permissions.IsAuthenticated(), CanAssignTask()]
        elif self.action == 'change_status':
            return [permissions.IsAuthenticated(), CanChangeStatus()]
        return [permissions.IsAuthenticated()]
        
    def get_queryset(self):
        """
        Get tasks for projects user has access to.
        
        Supports filtering by:
        - project_id: Filter by specific project
        - status: Filter by status (todo, in_progress, etc.)
        - assignee_id: Filter by assigned user
        - priority: Filter by priority level
        
        Laravel equivalent:
        public function index(Request $request) {
            return Task::query()
                ->whereHas('project', fn($q) => $q->whereBelongsToUser(auth()->user()))
                ->when($request->project_id, fn($q, $id) => $q->where('project_id', $id))
                ->when($request->status, fn($q, $s) => $q->where('status', $s))
                ->get();
        }
        """
        user = self.request.user
        
        # Base queryset: tasks from projects user has access to
        queryset = Task.objects.filter(
            Q(project__owner=user) | Q(project__memberships__user=user)
        ).distinct().select_related('assignee', 'created_by', 'project')
        
        # Apply filters from query params
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        task_status = self.request.query_params.get('status')
        if task_status:
            queryset = queryset.filter(status=task_status)
        
        assignee_id = self.request.query_params.get('assignee_id')
        if assignee_id:
            if assignee_id == 'unassigned':
                queryset = queryset.filter(assignee__isnull=True)
            else:
                queryset = queryset.filter(assignee_id=assignee_id)
        
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('position', '-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        elif self.action == 'retrieve':
            return TaskWithCommentsSerializer
        return TaskSerializer
    
    # ==========================================================================
    # Custom Actions
    # ==========================================================================
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """
        Reorder task (for Kanban drag-drop).
        
        POST /api/tasks/{id}/reorder/
        Body: { "status": "in_progress", "position": 2 }
        
        Laravel equivalent:
        public function reorder(Request $request, Task $task) {
            $task->update([
                'status' => $request->status,
                'position' => $request->position,
            ]);
            
            // Reorder other tasks
            Task::where('project_id', $task->project_id)
                ->where('status', $request->status)
                ->where('id', '!=', $task->id)
                ->where('position', '>=', $request->position)
                ->increment('position');
                
            return $task;
        }
        """
        task = self.get_object()
        serializer = TaskReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        new_position = serializer.validated_data['position']
        
        old_status = task.status
        old_position = task.position
        
        # Update task
        task.status = new_status
        task.position = new_position
        task.save()
        
        # Reorder other tasks in the same column
        if old_status == new_status:
            # Moving within same column
            if new_position < old_position:
                # Moving up: increment positions of tasks in between
                Task.objects.filter(
                    project=task.project,
                    status=new_status,
                    position__gte=new_position,
                    position__lt=old_position
                ).exclude(id=task.id).update(position=F('position') + 1)
            else:
                # Moving down: decrement positions of tasks in between
                Task.objects.filter(
                    project=task.project,
                    status=new_status,
                    position__gt=old_position,
                    position__lte=new_position
                ).exclude(id=task.id).update(position=F('position') - 1)
        else:
            # Moving to different column
            # Decrement positions in old column
            Task.objects.filter(
                project=task.project,
                status=old_status,
                position__gt=old_position
            ).update(position=F('position') - 1)
            
            # Increment positions in new column
            Task.objects.filter(
                project=task.project,
                status=new_status,
                position__gte=new_position
            ).exclude(id=task.id).update(position=F('position') + 1)
        
        return Response(TaskSerializer(task).data)
    
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """
        Get or add comments to a task.
        
        GET  /api/tasks/{id}/comments/  - List comments
        POST /api/tasks/{id}/comments/  - Add comment
        
        Laravel equivalent:
        public function comments(Task $task) {
            return CommentResource::collection($task->comments);
        }
        
        public function addComment(Request $request, Task $task) {
            $comment = $task->comments()->create([
                'user_id' => auth()->id(),
                'content' => $request->content,
            ]);
            return new CommentResource($comment);
        }
        """
        task = self.get_object()
        
        if request.method == 'GET':
            comments = task.comments.select_related('user')
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = CommentCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            comment = Comment.objects.create(
                task=task,
                user=request.user,
                content=serializer.validated_data['content']
            )
            
            return Response(
                CommentSerializer(comment).data,
                status=status.HTTP_201_CREATED
            )
            
            
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, CanAssignTask])
    def assign(self, request, pk=None):
        """
        Assign task to user
        
        POST api/tasks/{id}/assign
        Body: {"assignee":2}
        
        Rules:
        - owner/Admin can assign to any project member
        - Members can only assign to themselved
        - Assignee must be project memebr
        """
        
        task = self.get_object()
        assignee_id = request.data.get("assignee")
        
        if assignee_id is None:
            task.assignee = None
            task.save()
            return Response({
                'message': 'Task unassigned',
                'task': TaskSerializer(task).data,
                'assignee_id': assignee_id
            })
            
        # Validate assignee is a project member
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            assignee = User.objects.get(id=assignee_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        is_member = {
            task.project.owner == assignee or
            task.project.memberships.filter(user=assignee).exists()
        }
        
        if not is_member:
            return Response(
                {'error': 'User is not a member of this project'},
                status=status.HTTP_400_BAD_REQUEST 
            )
            
        task.assignee = assignee
        task.save()
        
        return Response({
            'message': f'Task assigned to {assignee.email}',
            'task': TaskSerializer(task).data
        })
        
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTaskProjectMember, IsProjectAdmin])
    def change_status(self, request, pk=None):
        """
        Change status of the task if user is assignee, admin or owner of the project
        """
        task = self.get_object()
        
        new_status = request.data.get('status')
        
        if new_status == None:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        valid_statuses = [choice[0] for choice in Task.Status.choices]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        task.status = new_status
        task.save()
        
        return Response({
            'message': f"Status changed for '{task.title}' to {new_status}",
            'task' : TaskSerializer(task).data
        })
        
    @action(detail=True, methods=['post','delete'])
    def labels(self, request, pk=None):
        """
        Add/remove labels from task
        POST /api/tasks/{id}/labels/   - Add label
        DELETE /api/tasks/{id}/labels/ - Remove label
        
        Body: {"label_id": 1}
        """
        task = self.get_object()
        label_id = request.data.get('label_id')
        
        if not label_id:
            return Response({
                'error': 'Label is required'
            },
            status  = status.HTTP_400_BAD_REQUEST)
            
        try:
            label = Label.objects.get(id=label_id, project=task.project)
        except Label.DoesNotExist:
            return Response(
                {'error': 'Label not found in this project'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if request.method == 'POST':
            label.tasks.add(task)
            return Response({
                'message': f'Label {label.name} added to a task',
                'task': TaskSerializer(task).data
            })
        elif request.method == 'DELETE':
            label.tasks.remove(task)
            return Response({
                'message': f'Label {label.name} removed from a task',
                'task': TaskSerializer(task).data
            })
        
        
class LabelViewSet(viewsets.ModelViewSet):
    """
    Crud for Labels.
    Labels belong to a project and can be attached to multiple tasks.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Label.objects.all()
    
    def get_queryset(self):
        """Get labels for projects user has access to."""
        user = self.request.user
        return Label.objects.filter(
            Q(project__owner = user) | Q(project__memberships__user=user)
        ).distinct()
        
    def get_serializer_class(self):
        if self.action == 'create':
            return LabelCreateSerializer
        elif self.action in ['update','partial_udpate']:
            return LabelUpdateSerializer
        return LabelSerializer
    
class CommentViewSet(viewsets.ModelViewSet):
    """CRUD for comment"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Comment.objects.all()
    
    def get_queryset(self):
        """Get comments for tasks user has access to."""
        user = self.request.user
        return Comment.objects.filter(
            Q(task__project__owner=user) | Q(task__project__memberships__user=user)
        ).distinct().select_related('user','task')
        
    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        """ser user when creating comment"""
        serializer.save(user=self.request.user)
    