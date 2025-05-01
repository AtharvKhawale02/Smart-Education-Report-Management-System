from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('Principal', 'Principal'),
        ('HOD', 'HOD'),
        ('Faculty', 'Faculty'),
    ]
    full_name = models.CharField(max_length=255, default='Default Name')  # New field for full name
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    hod = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hod_department'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='departments',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['hod'], name='unique_hod_per_department')
        ]
    
    def clean(self):
        if self.hod and Department.objects.filter(hod=self.hod).exclude(id=self.id).exists():
            raise ValidationError(f"{self.hod} is already assigned as HOD to another department.")
    
    def save(self, *args, **kwargs):
        self.clean()  # Validat e before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name




class Task(models.Model):
    ROLE_CHOICES = [
        ('Principal', 'Principal'),
        ('HOD', 'HOD'),
        ('Faculty', 'Faculty'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks'
    )
    assigned_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Faculty')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_tasks'
    )
    due_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Completed', 'Completed')],
        default='Pending'
    )
    parent_task = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_tasks'
    )
    progress = models.IntegerField(default=0)  # Progress percentage (0-100)
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on every save
    def __str__(self):
        return self.title

class AcademicYear(models.Model):
    start_year = models.PositiveIntegerField(default=2024)
    end_year = models.PositiveIntegerField(default=2025)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.start_year}-{self.end_year}"

class Report(models.Model):
    REPORT_TYPES = [
        ('Attendance', 'Attendance'),
        ('Feedback', 'Feedback'),
        ('Exam', 'Exam'),
        ('R&D / IPR', 'R&D / IPR'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted to HOD'),
        ('approved', 'Approved by HOD'),
        ('rejected', 'Rejected by HOD'),
    ]
    
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(
        upload_to='reports/',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls', 'pdf'])]
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
        null=True,
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='department_reports'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.report_type} ({self.status})"

class AnnualDepartmentReport(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted to Principal'),
        ('approved', 'Approved by Principal'),
        ('rejected', 'Rejected by Principal'),
    ]
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    compiled_file = models.FileField(upload_to='annual_reports/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('department', 'academic_year')

    def __str__(self):
        return f"Annual Report - {self.department.name} ({self.academic_year})"








class Comment(models.Model):
    report = models.ForeignKey('Report', on_delete=models.CASCADE)
    commented_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.commented_by} commented on {self.report}"

        
