from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from django.contrib.auth.models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError

# Create your views here.
def home(request):
    return render(request, 'index.html')



@login_required(login_url='/login/')
def register_user(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')  # Fetch full name
        username = request.POST.get('username')  # Fetch username
        role = request.POST.get('role')
        email = request.POST.get('email')
        password = request.POST.get('password')
        department_id = request.POST.get('department')

        try:
            # If role is HOD, check if the department already has an HOD
            if role == 'HOD':
                department = Department.objects.get(id=department_id)
                if department.hod:
                    # Department already has an HOD, do not allow new HOD
                    messages.error(request, "This department already has an HOD!")
                    return redirect('register_user')
            
            # Create user only if no issues with the department
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                full_name=full_name,  # Save full name
                role=role,
                password=password
            )

            # Assign user to department if role is Faculty
            if role == 'Faculty':
                department = Department.objects.get(id=department_id)
                department.members.add(user)

            # Assign HOD only if no existing HOD for that department
            elif role == 'HOD':
                department.hod = user  # Assign the HOD to the department
                department.save()

            messages.success(request, f"User {full_name} registered successfully!")
            return redirect('register_user')

        except Department.DoesNotExist:
            messages.error(request, "The selected department does not exist.")
            return redirect('register_user')
        except IntegrityError:
            messages.error(request, "There was an error while creating the user.")
            return redirect('register_user')

    # For GET request: fetch role options and departments
    departments = Department.objects.all()
    role_options = []

    if request.user.role == 'Principal':
        role_options = ['HOD', 'Faculty']
    elif request.user.role == 'HOD':
        role_options = ['Faculty']
        departments = Department.objects.filter(hod=request.user)

    return render(request, 'register_user.html', {
        'role_options': role_options,
        'departments': departments
    })




def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:  # Check if authentication was successful
            login(request, user)
            # Redirect based on user role
            if user.role == 'Principal':
                return redirect('principal_dashboard')  # Change to your principal dashboard URL
            elif user.role == 'HOD':
                return redirect('hod_dashboard')  # Change to your HOD dashboard URL
            elif user.role == 'Faculty':
                return redirect('faculty_dashboard')  # Change to your faculty dashboard URL
            else:
                messages.error(request, "Invalid role.")
                return redirect('login')
        else:
            messages.error(request, "Invalid credentials.")
            return redirect('login')

    return render(request, 'login.html')

@login_required(login_url='/login/')
def logout_user(request):
    logout(request)
    return redirect('/login/')


def register(request):
    return render(request, 'register.html')

def is_principal(user):
    return user.role == 'Principal'

def is_hod(user):
    return user.role == 'HOD'

def is_faculty(user):
    return user.role == 'Faculty'

# Dashboard views
@login_required
@user_passes_test(is_principal)
def principal_dashboard(request):
    # Get all department reports
    annual_reports = AnnualDepartmentReport.objects.all().order_by('-created_at')
    
    # Get overall statistics
    departments = Department.objects.all()
    report_stats = {
        'total_departments': departments.count(),
        'total_reports': Report.objects.count(),
        'pending_reports': Report.objects.filter(status='submitted').count(),
        'approved_reports': Report.objects.filter(status='approved').count()
    }
    
    # Get department-wise report status
    department_stats = []
    for dept in departments:
        dept_stats = {
            'name': dept.name,
            'total_reports': Report.objects.filter(department=dept).count(),
            'pending_reports': Report.objects.filter(department=dept, status='submitted').count(),
            'approved_reports': Report.objects.filter(department=dept, status='approved').count(),
            'annual_report': AnnualDepartmentReport.objects.filter(department=dept).first()
        }
        department_stats.append(dept_stats)

    context = {
        'annual_reports': annual_reports,
        'report_stats': report_stats,
        'department_stats': department_stats
    }
    
    return render(request, 'principal_dashboard.html', context)

@login_required
@user_passes_test(is_hod)
def hod_dashboard(request):
    return render(request, 'hod_dashboard.html')

@login_required
@user_passes_test(is_faculty)
def faculty_dashboard(request):
    return render(request, 'faculty_dashboard.html')



@login_required
@user_passes_test(lambda u: u.role == 'Principal')
def manage_departments(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        Department.objects.create(name=name, description=description)
        messages.success(request, "Department created successfully!")
        return redirect('manage_departments')

    return render(request, 'manage_departments.html', {'departments': departments})


@login_required
@user_passes_test(is_hod)
def manage_members(request):
    department = Department.objects.get(hod=request.user)
    faculty_members = department.members.all()
    all_faculty = CustomUser.objects.filter(role='Faculty').exclude(id__in=faculty_members)

    if request.method == 'POST':
        action = request.POST.get('action')
        faculty_id = request.POST.get('faculty')
        faculty = CustomUser.objects.get(id=faculty_id)
        
        if action == 'add':
            department.members.add(faculty)
            messages.success(request, f"{faculty.username} added to the department.")
        elif action == 'remove':
            department.members.remove(faculty)
            messages.success(request, f"{faculty.username} removed from the department.")
        
        return redirect('manage_members')

    return render(request, 'manage_members.html', {
        'department': department,
        'faculty_members': faculty_members,
        'all_faculty': all_faculty
    })



@login_required
@user_passes_test(is_principal)
def assign_task_to_hod(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')

        assigned_to = CustomUser.objects.get(id=assigned_to_id)

        Task.objects.create(
            title=title,
            description=description,
            assigned_to=assigned_to,
            created_by=request.user,
            due_date=due_date,
            assigned_role='HOD'
        )
        messages.success(request, "Task assigned to HOD successfully!")
        return redirect('principal_dashboard')

    # Get all HODs for task assignment
    hods = CustomUser.objects.filter(role='HOD')
    return render(request, 'assign_task_to_hod.html', {'hods': hods})


# HOD views their tasks
@login_required
@user_passes_test(is_hod)
def view_hod_tasks(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    return render(request, 'hod_dashboard.html', {'tasks': tasks})

# Faculty views their tasks
@login_required
@user_passes_test(is_faculty)
def view_faculty_tasks(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    return render(request, 'view_faculty_tasks.html', {'tasks': tasks})

@login_required
@user_passes_test(is_hod)
def delegate_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    faculty_members = CustomUser.objects.filter(role='Faculty', departments__hod=request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')

        assigned_to = CustomUser.objects.get(id=assigned_to_id)
        Task.objects.create(
            title=title,
            description=description,
            assigned_to=assigned_to,
            assigned_role='Faculty',
            created_by=request.user,
            due_date=due_date,
            parent_task=task
        )
        messages.success(request, f"Task '{title}' delegated to {assigned_to.full_name}.")
        return redirect('view_hod_tasks')

    return render(request, 'delegate_task.html', {'task': task, 'faculty_members': faculty_members})


@login_required
@user_passes_test(is_hod)
def create_task_for_faculty(request):
    # Get the HOD's department
    department = get_object_or_404(Department, hod=request.user)
    faculty_members = department.members.filter(role='Faculty')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')

        assigned_to = CustomUser.objects.get(id=assigned_to_id)
        Task.objects.create(
            title=title,
            description=description,
            assigned_to=assigned_to,
            assigned_role='Faculty',
            created_by=request.user,
            due_date=due_date
        )

        messages.success(request, f"Task '{title}' assigned to {assigned_to.full_name}.")
        return redirect('create_task_for_faculty')

    return render(request, 'create_task_for_faculty.html', {
        'faculty_members': faculty_members,
    })



from django.db.models import Count, Q

@login_required
def analytics_dashboard(request):
    # Get current academic year
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Department-wise report statistics
    dept_stats = DepartmentReport.objects.filter(
        academic_year=current_year
    ).values('department__name').annotate(
        total_reports=Count('id'),
        approved_reports=Count('id', filter=Q(status='approved')),
        pending_reports=Count('id', filter=Q(status__in=['draft', 'submitted'])),
        rejected_reports=Count('id', filter=Q(status='rejected'))
    )
    
    # Monthly submission trends
    monthly_trends = DepartmentReport.objects.filter(
        academic_year=current_year
    ).annotate(
        month=TruncMonth('submitted_at')
    ).values('month').annotate(
        submissions=Count('id')
    ).order_by('month')
    
    # Section-wise statistics
    section_stats = DepartmentReport.objects.filter(
        academic_year=current_year
    ).values('section__name').annotate(
        total=Count('id'),
        completion_rate=Count('id', filter=Q(status='approved')) * 100.0 / Count('id')
    )
    
    context = {
        'dept_stats': dept_stats,
        'monthly_trends': monthly_trends,
        'section_stats': section_stats,
        'academic_year': current_year,
    }
    
    return render(request, 'analytics.html', context)


@login_required
def update_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        progress = request.POST.get('progress')
        
        if status in ['Pending', 'In Progress', 'Completed'] and 0 <= int(progress) <= 100:
            task.status = status
            task.progress = progress
            task.save()
            messages.success(request, "Task updated successfully!")
        else:
            messages.error(request, "Invalid input for task update.")
        
        return redirect('view_hod_tasks' if request.user.role == 'HOD' else 'view_faculty_tasks')

    return render(request, 'update_task.html', {'task': task})

@login_required
def add_comment(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        Comment.objects.create(report=report, commented_by=request.user, comment=comment_text)
        messages.success(request, "Comment added successfully.")
    return redirect('view_comments', report_id=report_id)

# View Comments
@login_required
def view_comments(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    comments = Comment.objects.filter(report=report)
    return render(request, 'view_comments.html', {'report': report, 'comments': comments})



from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from openpyxl import load_workbook
import io

@login_required
@user_passes_test(is_faculty)
def submit_report(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        report_type = request.POST.get('report_type')
        description = request.POST.get('description')
        file = request.FILES.get('report_file')
        current_year = AcademicYear.objects.get(is_current=True)
        
        # Get faculty's department
        department = request.user.departments.first()
        
        report = Report.objects.create(
            title=title,
            report_type=report_type,
            description=description,
            file=file,
            submitted_by=request.user,
            department=department,
            status='submitted',
            academic_year=current_year
        )
        
        messages.success(request, "Report submitted successfully for HOD approval.")
        return redirect('faculty_dashboard')
        
    return render(request, 'submit_report.html', {
        'report_types': Report.REPORT_TYPES
    })

@login_required
@user_passes_test(is_hod)
def review_reports(request):
    department = Department.objects.get(hod=request.user)
    pending_reports = Report.objects.filter(
        department=department,
        status='submitted'
    ).order_by('-created_at')
    
    return render(request, 'review_reports.html', {
        'pending_reports': pending_reports
    })

@login_required
@user_passes_test(is_hod)
def approve_reject_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)  # Correct variable name

    if request.method == 'POST':
        action = request.POST.get('action')
        feedback = request.POST.get('feedback')

        if action in ['approve', 'reject']:
            report.status = 'approved' if action == 'approve' else 'rejected'
            report.feedback = feedback
            report.save()
            messages.success(request, f"Report {action}d successfully.")
        else:
            messages.error(request, "Invalid action.")

        return redirect('review_reports')

    return render(request, 'approve_reject_report.html', {'report': report, 'feedback': report.feedback})  # Pass 'report' here



@login_required
@user_passes_test(is_hod)
def generate_annual_report(request):
    department = Department.objects.get(hod=request.user)
    current_year = AcademicYear.objects.get(is_current=True)
    
    # Check if all reports are approved
    pending_reports = Report.objects.filter(
        department=department,
        academic_year=current_year
    ).exclude(status='approved').exists()
    
    if pending_reports:
        messages.error(request, "All reports must be approved before generating annual report.")
        return redirect('review_reports')
    
    if request.method == 'POST':
        # Create annual report
        annual_report = AnnualDepartmentReport.objects.create(
            department=department,
            academic_year=current_year,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            status='draft'
        )
        
        # Generate PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content to PDF
        p.drawString(100, 750, f"Annual Department Report - {department.name}")
        p.drawString(100, 700, f"Academic Year: {current_year}")
        
        y_position = 650
        for report_type, _ in Report.REPORT_TYPES:
            reports = Report.objects.filter(
                department=department,
                academic_year=current_year,
                report_type=report_type,
                status='approved'
            )
            
            p.drawString(100, y_position, f"\n{report_type} Reports Summary:")
            y_position -= 20
            
            for report in reports:
                p.drawString(120, y_position, f"- {report.title}")
                y_position -= 15
        
        p.save()
        buffer.seek(0)
        annual_report.compiled_file.save(f'annual_report_{department.name}_{current_year}.pdf', buffer)
        
        messages.success(request, "Annual report generated successfully.")
        return redirect('view_annual_report')
    
    return render(request, 'generate_annual_report.html')

@login_required
@user_passes_test(is_hod)
def submit_annual_report(request, report_id):
    annual_report = get_object_or_404(AnnualDepartmentReport, id=report_id)
    
    if request.method == 'POST':
        annual_report.status = 'submitted'
        annual_report.submitted_at = timezone.now()
        annual_report.save()
        
        messages.success(request, "Annual report submitted to principal successfully.")
        return redirect('hod_dashboard')
    
    return render(request, 'submit_annual_report.html', {'annual_report': annual_report})

@login_required
@user_passes_test(is_principal)
def view_department_reports(request):
    annual_reports = AnnualDepartmentReport.objects.filter(
        status='submitted'
    ).order_by('-submitted_at')
    
    return render(request, 'view_department_reports.html', {
        'annual_reports': annual_reports
    })

def convert_excel_to_pdf(excel_file):
    # Load Excel file
    wb = load_workbook(excel_file)
    ws = wb.active
    
    # Create PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Convert Excel content to PDF
    y_position = 750
    for row in ws.rows:
        x_position = 50
        for cell in row:
            p.drawString(x_position, y_position, str(cell.value))
            x_position += 100
        y_position -= 20
        
    p.save()
    buffer.seek(0)
    return buffer



@login_required
def view_report_status(request):
    if request.user.role == 'Faculty':
        reports = Report.objects.filter(
            submitted_by=request.user
        ).order_by('-created_at')
    elif request.user.role == 'HOD':
        department = Department.objects.get(hod=request.user)
        reports = Report.objects.filter(
            department=department
        ).order_by('-created_at')
    else:  # Principal
        reports = Report.objects.all().order_by('-created_at')
    
    return render(request, 'view_report_status.html', {'reports': reports})

@login_required
@user_passes_test(is_hod)
def track_department_reports(request):
    department = Department.objects.get(hod=request.user)
    current_year = AcademicYear.objects.get(is_current=True)
    
    report_stats = {
        'total': Report.objects.filter(department=department, academic_year=current_year).count(),
        'pending': Report.objects.filter(department=department, academic_year=current_year, status='submitted').count(),
        'approved': Report.objects.filter(department=department, academic_year=current_year, status='approved').count(),
        'rejected': Report.objects.filter(department=department, academic_year=current_year, status='rejected').count(),
    }
    
    report_types_status = {}
    for report_type, _ in Report.REPORT_TYPES:
        report_types_status[report_type] = {
            'total': Report.objects.filter(
                department=department,
                academic_year=current_year,
                report_type=report_type
            ).count(),
            'approved': Report.objects.filter(
                department=department,
                academic_year=current_year,
                report_type=report_type,
                status='approved'
            ).count()
        }
    
    return render(request, 'track_department_reports.html', {
        'report_stats': report_stats,
        'report_types_status': report_types_status
    })

@login_required
@user_passes_test(is_principal)
def review_annual_report(request, report_id):
    annual_report = get_object_or_404(AnnualDepartmentReport, id=report_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        feedback = request.POST.get('feedback')
        
        if action == 'approve':
            annual_report.status = 'approved'
        elif action == 'reject':
            annual_report.status = 'rejected'
        
        annual_report.feedback = feedback
        annual_report.save()
        
        # Send notification to HOD
        send_mail(
            f'Annual Report {annual_report.status.title()}',
            f'Your annual report has been {annual_report.status}.\n\nFeedback: {feedback}',
            settings.DEFAULT_FROM_EMAIL,
            [annual_report.department.hod.email],
            fail_silently=False,
        )
        
        messages.success(request, f"Annual report {action}d successfully.")
        return redirect('view_department_reports')
    
    return render(request, 'review_annual_report.html', {'annual_report': annual_report})

@login_required
def download_converted_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    if not (request.user == report.submitted_by or 
            request.user == report.department.hod or 
            request.user.role == 'Principal'):
        return HttpResponseForbidden("You don't have permission to access this report.")
    
    # Check if file is Excel and needs conversion
    if report.file.name.endswith(('.xlsx', '.xls')):
        pdf_buffer = convert_excel_to_pdf(report.file)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
        response.write(pdf_buffer.getvalue())
        
        return response
    else:
        # If already PDF, just serve the file
        response = HttpResponse(report.file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
        return response