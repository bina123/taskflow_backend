# Django Learning Guide for Laravel Developers

## Step-by-Step Understanding of TaskFlow AI Project

---

## 📁 Project Structure Explained

```
taskflow-backend/
├── config/                  # Laravel: config/ folder
│   ├── settings.py          # Laravel: config/app.php + config/database.php + etc.
│   ├── urls.py              # Laravel: routes/web.php + routes/api.php
│   └── wsgi.py              # Server entry point
│
├── accounts/                # Laravel: app/Models/User.php + related files
│   ├── models.py            # Laravel: app/Models/User.php
│   ├── serializers.py       # Laravel: app/Http/Resources/ + app/Http/Requests/
│   ├── views.py             # Laravel: app/Http/Controllers/AuthController.php
│   ├── urls.py              # Laravel: Route group for auth
│   └── admin.py             # Laravel: Nova/Filament resource
│
├── projects/                # Feature module (like Laravel packages)
│   ├── models.py            # app/Models/Project.php
│   ├── serializers.py       # app/Http/Resources/ProjectResource.php
│   ├── views.py             # app/Http/Controllers/ProjectController.php
│   ├── urls.py              # Route::apiResource('projects', ...)
│   └── admin.py             # Admin panel config
│
├── tasks/                   # Another feature module
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── manage.py                # Laravel: artisan
├── requirements.txt         # Laravel: composer.json
└── .env                     # Same as Laravel
```

---

## 🔄 Key Concepts Mapping: Laravel → Django

### 1. MODELS (models.py)

**Laravel:**
```php
// app/Models/Task.php
class Task extends Model {
    protected $fillable = ['title', 'description', 'status'];
    protected $casts = ['due_date' => 'date'];
    
    public function project() {
        return $this->belongsTo(Project::class);
    }
    
    public function comments() {
        return $this->hasMany(Comment::class);
    }
}
```

**Django:**
```python
# tasks/models.py
class Task(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    due_date = models.DateField(null=True, blank=True)
    
    # belongsTo = ForeignKey
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'  # This enables project.tasks.all()
    )
    
    # hasMany is AUTOMATIC via related_name on ForeignKey
    # Access comments via: task.comments.all()
```

**Key Differences:**
| Laravel | Django |
|---------|--------|
| `$fillable` / `$guarded` | Not needed - all fields are defined explicitly |
| `$casts` | Field types handle casting automatically |
| `belongsTo()` | `ForeignKey()` |
| `hasMany()` | Automatic via `related_name` on the child's ForeignKey |
| `belongsToMany()` | `ManyToManyField()` |
| `timestamps()` | `auto_now_add=True` / `auto_now=True` |

---

### 2. SERIALIZERS (serializers.py) = Resources + FormRequests

**Laravel Resource:**
```php
// app/Http/Resources/TaskResource.php
class TaskResource extends JsonResource {
    public function toArray($request) {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'assignee' => new UserResource($this->assignee),
            'comments_count' => $this->comments()->count(),
        ];
    }
}
```

**Laravel FormRequest:**
```php
// app/Http/Requests/StoreTaskRequest.php
class StoreTaskRequest extends FormRequest {
    public function rules() {
        return [
            'title' => 'required|string|max:300',
            'description' => 'nullable|string',
        ];
    }
}
```

**Django Serializer (BOTH in one):**
```python
# tasks/serializers.py
class TaskSerializer(serializers.ModelSerializer):
    """This is like Resource - for OUTPUT"""
    assignee = UserSerializer(read_only=True)  # Nested resource
    comments_count = serializers.SerializerMethodField()  # Computed field
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'assignee', 'comments_count']
    
    def get_comments_count(self, obj):
        return obj.comments.count()


class TaskCreateSerializer(serializers.ModelSerializer):
    """This is like FormRequest - for INPUT validation"""
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assignee']
    
    # Validation rules are automatic from model fields!
    # CharField(max_length=300) = 'required|string|max:300'
    # TextField(blank=True) = 'nullable|string'
```

---

### 3. VIEWS (views.py) = Controllers

**Laravel Controller:**
```php
class TaskController extends Controller {
    public function index(Request $request) {
        $tasks = Task::where('project_id', $request->project_id)->get();
        return TaskResource::collection($tasks);
    }
    
    public function store(StoreTaskRequest $request) {
        $task = Task::create($request->validated());
        return new TaskResource($task);
    }
    
    public function show(Task $task) {
        return new TaskResource($task);
    }
}
```

**Django View (3 types):**

#### Type 1: APIView (Most manual - like basic controller)
```python
class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(project_id=request.query_params.get('project_id'))
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task).data, status=201)
```

#### Type 2: Generic Views (Pre-built common operations)
```python
class TaskListCreateView(generics.ListCreateAPIView):
    """Handles both GET (list) and POST (create)"""
    queryset = Task.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateSerializer
        return TaskSerializer
```

#### Type 3: ViewSet (Like Resource Controller - RECOMMENDED)
```python
class TaskViewSet(viewsets.ModelViewSet):
    """
    Automatically provides: list, create, retrieve, update, destroy
    Like: Route::apiResource('tasks', TaskController::class);
    """
    queryset = Task.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer
    
    # Custom action (like additional route method)
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """POST /api/tasks/{id}/reorder/"""
        task = self.get_object()
        # ... reorder logic
        return Response(TaskSerializer(task).data)
```

---

### 4. URLS (urls.py) = routes/api.php

**Laravel:**
```php
// routes/api.php
Route::middleware('auth:sanctum')->group(function () {
    Route::apiResource('projects', ProjectController::class);
    Route::apiResource('tasks', TaskController::class);
    Route::post('/tasks/{task}/reorder', [TaskController::class, 'reorder']);
});
```

**Django:**
```python
# config/urls.py (main)
urlpatterns = [
    path('api/', include('projects.urls')),
    path('api/', include('tasks.urls')),
]

# tasks/urls.py
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
]
# This auto-generates all CRUD routes + custom actions!
```

---

## 🎓 What You MUST Understand First

### Priority 1: Models & ORM (Day 1-2)

**Learn these Django ORM operations:**

```python
# CREATE (Laravel: Task::create([...]))
task = Task.objects.create(title="New Task", project=project)

# READ ONE (Laravel: Task::find($id) or Task::findOrFail($id))
task = Task.objects.get(id=1)  # Raises DoesNotExist if not found
task = Task.objects.filter(id=1).first()  # Returns None if not found

# READ MANY (Laravel: Task::all() or Task::where(...)->get())
tasks = Task.objects.all()
tasks = Task.objects.filter(status='todo')
tasks = Task.objects.filter(project__owner=user)  # __ for relationships!

# UPDATE (Laravel: $task->update([...]))
task.title = "Updated Title"
task.save()
# OR
Task.objects.filter(id=1).update(title="Updated Title")

# DELETE (Laravel: $task->delete())
task.delete()
# OR
Task.objects.filter(id=1).delete()

# RELATIONSHIPS (Laravel: $task->project or $project->tasks)
task.project  # belongsTo - returns single object
project.tasks.all()  # hasMany - returns QuerySet

# FILTERING (Laravel: ->where())
Task.objects.filter(status='todo', priority='high')  # AND
Task.objects.filter(Q(status='todo') | Q(status='in_progress'))  # OR

# ORDERING (Laravel: ->orderBy())
Task.objects.order_by('-created_at')  # - means DESC
Task.objects.order_by('position', '-created_at')  # Multiple

# PAGINATION (Laravel: ->paginate())
# Handled automatically by DRF with PAGE_SIZE setting
```

### Priority 2: Serializers (Day 3)

**Key serializer patterns:**

```python
# 1. ModelSerializer - Auto-generates fields from model
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'status']  # Or '__all__'
        read_only_fields = ['id', 'created_at']

# 2. Nested serializers
class TaskSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)  # Full nested object
    project_id = serializers.IntegerField(write_only=True)  # Just ID for input
    
# 3. Computed fields
class TaskSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField()
    
    def get_comments_count(self, obj):
        return obj.comments.count()

# 4. Validation
class TaskSerializer(serializers.ModelSerializer):
    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title too short")
        return value
    
    def validate(self, attrs):  # Cross-field validation
        if attrs.get('due_date') and attrs['due_date'] < date.today():
            raise serializers.ValidationError("Due date cannot be in past")
        return attrs
```

### Priority 3: Views & Permissions (Day 4)

**Permission classes (like middleware):**

```python
from rest_framework import permissions

# Built-in permissions
permissions.AllowAny           # No auth required
permissions.IsAuthenticated    # Must be logged in
permissions.IsAdminUser        # Must be staff/admin

# Usage in views
class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    # OR different permissions per action
    def get_permissions(self):
        if self.action == 'list':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

# Custom permission (like Laravel Gate/Policy)
class IsProjectMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.project.memberships.filter(user=request.user).exists()
```

---

## 🚀 Your Day 1 Action Items

### Step 1: Run migrations and create superuser
```bash
cd taskflow-backend

# Create database tables (Laravel: php artisan migrate)
python manage.py makemigrations
python manage.py migrate

# Create admin user (Laravel: php artisan tinker + User::create)
python manage.py createsuperuser
# Enter: email, username, password

# Run server (Laravel: php artisan serve)
python manage.py runserver
```

### Step 2: Test the API

1. **Visit Admin Panel**: http://localhost:8000/admin/
   - Login with superuser credentials
   - Explore the interface (like Laravel Nova)

2. **Test Authentication**:
```bash
# Register a user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"Test123!@#","password_confirm":"Test123!@#","first_name":"Test","last_name":"User"}'

# Get JWT token (login)
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!@#"}'

# Use the token in subsequent requests
curl http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

3. **Test CRUD**:
```bash
# Create project
curl -X POST http://localhost:8000/api/projects/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My First Project","description":"Testing"}'

# List projects
curl http://localhost:8000/api/projects/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create task
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My First Task","project":1}'
```

### Step 3: Explore the code

1. **Read models.py** files - understand the data structure
2. **Read serializers.py** - see how data is validated and transformed
3. **Read views.py** - see how requests are handled
4. **Read urls.py** - see how URLs map to views

---

## 📚 Learning Resources (In Order)

1. **Django Official Tutorial** (2-3 hours)
   - https://docs.djangoproject.com/en/5.0/intro/tutorial01/
   - Complete parts 1-4 to understand Django basics

2. **DRF Tutorial** (2 hours)
   - https://www.django-rest-framework.org/tutorial/quickstart/
   - Learn API-specific concepts

3. **Build something small**
   - Add a new feature to TaskFlow (e.g., task labels)
   - This reinforces learning better than tutorials

---

## ❓ Common Questions

**Q: Where is the routes file?**
A: `config/urls.py` (main) + each app has its own `urls.py`

**Q: Where do I put business logic?**
A: In `views.py` or create a `services.py` file (like Laravel Services)

**Q: How do I access the current user?**
A: `request.user` (like Laravel's `auth()->user()` or `$request->user()`)

**Q: How do I run migrations?**
A: `python manage.py makemigrations` then `python manage.py migrate`

**Q: Where is the .env loaded?**
A: In `settings.py` using `python-dotenv` and `os.getenv()`

**Q: How do I add a new app/module?**
A: `python manage.py startapp appname` then add to `INSTALLED_APPS`

---

Good luck with your Django journey! 🎉
