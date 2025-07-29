"""
candidate_application_views.py

This module contains view functions for handling CandidateApplication 
HTTP requests and rendering responses.

This provides parallel functionality to the existing candidate views
but using the new CandidateApplication junction model for multiple
recruitments per candidate.
"""

import contextlib
import json
import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.models import User
from django.core import serializers
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from base.backends import ConfiguredEmailBackend
from base.methods import get_pagination, sortby, export_data
from employee.models import Employee
from horilla.decorators import hx_request_required, login_required, permission_required
from notifications.signals import notify
from recruitment.decorators import manager_can_enter
from recruitment.filters import CandidateApplicationFilter, InterviewScheduleApplicationFilter
from recruitment.forms import (
    ApplicationForm,
    CandidateApplicationCreationForm,
    CandidateApplicationDropDownForm,
    CandidateApplicationStageUpdateForm,
    CandidateApplicationUpdateForm,
    InterviewScheduleApplicationForm,
    StageNoteApplicationForm,
    SimpleCandidateApplicationForm,
    SimpleCandidateApplicationUpdateForm,
    CandidateApplicationExportForm,
)
from recruitment.models import (
    CandidateApplication,
    InterviewScheduleApplication,
    Recruitment,
    Stage,
    StageNoteApplication,
    JobPosition,
)
from recruitment.views.paginator_qry import paginator_qry

logger = logging.getLogger(__name__)


@login_required
@permission_required(perm="recruitment.add_candidateapplication")
def candidate_application_create(request):
    """
    This method is used to create candidate application
    """
    form = SimpleCandidateApplicationForm()
    
    if request.method == "POST":
        form = SimpleCandidateApplicationForm(request.POST)
        # Add debugging
        print("Form data:", request.POST)
        print("Form is valid:", form.is_valid())
        if not form.is_valid():
            print("Form errors:", form.errors)
            print("Form non-field errors:", form.non_field_errors())
        
        if form.is_valid():
            try:
                created_applications = form.save()
                if created_applications:
                    # Assign all created applications to the "sourced" stage
                    for application in created_applications:
                        recruitment = application.recruitment_id
                        if recruitment:
                            # Find the "sourced" stage for this recruitment
                            sourced_stage = Stage.objects.filter(
                                recruitment_id=recruitment,
                                stage_type="sourced"
                            ).first()
                            if sourced_stage:
                                application.stage_id = sourced_stage
                                application.save()
                    
                    messages.success(
                        request, 
                        _("Successfully created {} candidate application(s) and assigned to sourced stage.").format(len(created_applications))
                    )
                else:
                    messages.warning(
                        request, 
                        _("No new applications were created. Applications may already exist for the selected candidates.")
                    )
                return redirect("candidate-application-view")
            except Exception as e:
                messages.error(request, _("Error creating candidate applications: {}").format(str(e)))
    
    context = {
        "form": form,
    }
    return render(
        request,
        "candidate_application/candidate_application_create_form.html",
        context,
    )


@login_required
@permission_required(perm="recruitment.view_candidateapplication")
def candidate_application_view(request):
    """
    This method renders all candidate applications to the template
    """
    view_type = request.GET.get("view")
    previous_data = request.GET.urlencode()
    candidate_applications = CandidateApplication.objects.filter(is_active=True)
    recruitments = Recruitment.objects.filter(closed=False, is_active=True)

    # Get emails that already exist as users
    mails = list(CandidateApplication.objects.values_list("email", flat=True))
    existing_emails = list(
        User.objects.filter(username__in=mails).values_list("email", flat=True)
    )

    filter_obj = CandidateApplicationFilter(request.GET, queryset=candidate_applications)
    if CandidateApplication.objects.exists():
        template = "candidate_application/candidate_application_view.html"
    else:
        template = "candidate_application/candidate_application_empty.html"

    candidate_applications = sortby(request, filter_obj.qs, "orderby")
    
    # Pagination
    page_number = request.GET.get("page")
    candidate_applications = paginator_qry(candidate_applications, page_number)

    requests_ids = json.dumps(
        [instance.id for instance in filter_obj.qs.filter(is_active=True)]
    )
    
    # Group by fields for the dropdown
    gp_fields = [
        ("recruitment_id", _("Recruitment")),
        ("stage_id", _("Stage")),
        ("job_position_id", _("Job Position")),
        ("hired", _("Hired")),
        ("canceled", _("Canceled")),
        ("converted", _("Converted")),
        ("is_active", _("Is Active")),
    ]
    
    context = {
        "candidate_applications": candidate_applications,
        "pd": previous_data,
        "filter_obj": filter_obj,
        "requests_ids": requests_ids,
        "view_type": view_type,
        "gp_fields": gp_fields,
        "recruitments": recruitments,
        "existing_emails": existing_emails,
    }
    return render(request, template, context)


@login_required
@permission_required(perm="recruitment.view_candidateapplication")
def candidate_application_view_individual(request, app_id):
    """
    This method is used to view individual candidate application
    """
    candidate_app = get_object_or_404(CandidateApplication, id=app_id)
    
    context = {
        "candidate_app": candidate_app,
        "interviews": candidate_app.candidate_application_interview.all(),
        "notes": candidate_app.stagenoteapplication_set.all().order_by("-id"),
    }
    return render(
        request, 
        "candidate_application/candidate_application_individual_view.html", 
        context
    )


@login_required
@permission_required(perm="recruitment.change_candidateapplication")
def candidate_application_update(request, app_id):
    """
    This method is used to update candidate application
    """
    candidate_app = get_object_or_404(CandidateApplication, id=app_id)
    form = SimpleCandidateApplicationUpdateForm(instance=candidate_app)
    
    if request.method == "POST":
        form = SimpleCandidateApplicationUpdateForm(
            request.POST, instance=candidate_app
        )
        if form.is_valid():
            form.save()
            messages.success(request, _("Candidate application updated successfully."))
            return redirect("candidate-application-view")
    
    context = {
        "form": form,
        "candidate_app": candidate_app,
    }
    return render(
        request, 
        "candidate_application/candidate_application_create_form.html", 
        context
    )


@login_required
@manager_can_enter(perm="recruitment.change_candidateapplication")
def candidate_application_stage_update(request, app_id):
    """
    This method is used to update candidate application stage when drag and drop
    the application from one stage to another on the pipeline template
    """
    stage_id = request.POST["stageId"]
    candidate_app = CandidateApplication.objects.get(id=app_id)
    stage_obj = Stage.objects.get(id=stage_id)
    
    # Check permissions
    from recruitment.decorators import is_recruitmentmanager, is_stagemanager
    stage_manager_on_this_recruitment = (
        is_stagemanager(request)[1]
        .filter(recruitment_id=stage_obj.recruitment_id)
        .exists()
    )
    
    if (
        stage_manager_on_this_recruitment
        or request.user.is_superuser
        or is_recruitmentmanager(rec_id=stage_obj.recruitment_id.id)[0]
    ):
        candidate_app.stage_id = stage_obj
        candidate_app.hired = stage_obj.stage_type == "selected"
        candidate_app.canceled = stage_obj.stage_type == "cancelled"
        candidate_app.start_onboard = False
        candidate_app.save()
        
        # Send notifications
        with contextlib.suppress(Exception):
            managers = stage_obj.stage_managers.select_related("employee_user_id")
            users = [employee.employee_user_id for employee in managers]
            notify.send(
                request.user.employee_get,
                recipient=users,
                verb=f"Candidate application moved to stage {stage_obj.stage}",
                icon="person-add",
                redirect=reverse("candidate-application-pipeline"),
            )

        return JsonResponse(
            {"type": "success", "message": _("Candidate application stage updated")}
        )
    return JsonResponse(
        {"type": "danger", "message": _("Something went wrong, Try again.")}
    )


@login_required
@permission_required(perm="recruitment.view_candidateapplication")
def candidate_application_pipeline(request):
    """
    This method is used to render candidate application pipeline view
    """
    recruitments = Recruitment.objects.filter(closed=False, is_active=True)
    form = CandidateApplicationDropDownForm()
    
    # Get all stages and applications
    candidate_applications = CandidateApplication.objects.filter(is_active=True)
    stages = Stage.objects.filter(recruitment_id__in=recruitments)
    
    # Group applications by stage
    pipeline_data = {}
    for stage in stages:
        pipeline_data[stage.id] = {
            'stage': stage,
            'applications': candidate_applications.filter(stage_id=stage).order_by('sequence')
        }
    
    context = {
        'recruitments': recruitments,
        'pipeline_data': pipeline_data,
        'form': form,
    }
    return render(request, "candidate_application/pipeline.html", context)


@login_required
@hx_request_required
@manager_can_enter(perm="recruitment.add_stagenoteapplication")
def add_note_application(request, app_id=None):
    """
    This method renders template component to add candidate application note
    """
    form = StageNoteApplicationForm(initial={"candidate_application_id": app_id})
    if request.method == "POST":
        form = StageNoteApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            note, attachment_ids = form.save(commit=False)
            candidate_app = CandidateApplication.objects.get(id=app_id)
            note.candidate_application_id = candidate_app
            note.stage_id = candidate_app.stage_id
            note.updated_by = request.user.employee_get
            note.save()
            note.stage_files.set(attachment_ids)
            messages.success(request, _("Note added successfully."))
    
    candidate_app = CandidateApplication.objects.get(id=app_id)
    return render(
        request,
        "candidate_application/individual_view_note.html",
        {
            "candidate_app": candidate_app,
            "note_form": form,
        },
    )


@login_required
@hx_request_required
@manager_can_enter(perm="recruitment.add_interviewscheduleapplication")
def interview_schedule_application(request, app_id):
    """
    This method is used to schedule interview for candidate application
    """
    candidate_app = get_object_or_404(CandidateApplication, id=app_id)
    form = InterviewScheduleApplicationForm()
    
    if request.method == "POST":
        form = InterviewScheduleApplicationForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.candidate_application_id = candidate_app
            interview.save()
            form.save_m2m()  # Save the many-to-many employee relationships
            
            # Automatically add stage interviewers if the candidate has a stage
            if candidate_app.stage_id and candidate_app.stage_id.stage_interviewers.exists():
                stage_interviewers = candidate_app.stage_id.stage_interviewers.all()
                for interviewer in stage_interviewers:
                    if interviewer not in interview.employee_id.all():
                        interview.employee_id.add(interviewer)
            
            messages.success(request, _("Interview scheduled successfully."))
            return redirect("candidate-application-view-individual", app_id=app_id)
    
    context = {
        "form": form,
        "candidate_app": candidate_app,
    }
    return render(
        request, 
        "candidate_application/interview_schedule_form.html", 
        context
    )


@login_required
@permission_required(perm="recruitment.view_interviewscheduleapplication")
def interview_view_application(request):
    """
    This method renders all interview schedules for candidate applications
    """
    interviews = InterviewScheduleApplication.objects.all()
    filter_obj = InterviewScheduleApplicationFilter(request.GET, queryset=interviews)
    
    interviews = sortby(request, filter_obj.qs, "orderby")
    
    # Pagination
    page_number = request.GET.get("page")
    interviews = get_pagination(request, interviews)
    
    context = {
        "interviews": interviews,
        "filter_obj": filter_obj,
    }
    return render(request, "candidate_application/interview_view.html", context)


@transaction.atomic
@login_required
@manager_can_enter(perm="recruitment.change_candidateapplication")
def candidate_application_conversion(request, app_id):
    """
    Convert CandidateApplication to Employee
    """
    candidate_app = get_object_or_404(CandidateApplication, id=app_id)

    if candidate_app.converted_employee_id:
        messages.info(request, "This candidate application is already converted to an employee.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    user_exists = User.objects.filter(username=candidate_app.email).exists()
    employee_exists = Employee.objects.filter(
        employee_user_id__username=candidate_app.email
    ).exists()

    if user_exists:
        messages.error(request, "User instance with this mail already exists")
    elif not employee_exists:
        try:
            # Create new employee
            new_employee = Employee(
                employee_first_name=candidate_app.name,
                email=candidate_app.email,
                phone=candidate_app.mobile,
                gender=candidate_app.gender,
                is_directly_converted=True,
            )
            new_employee.save()

            # Set work information
            work_info = new_employee.employee_work_info
            work_info.job_position_id = candidate_app.job_position_id
            work_info.department_id = candidate_app.job_position_id.department_id
            work_info.company_id = candidate_app.recruitment_id.company_id
            work_info.save()

            # Link to candidate application
            candidate_app.converted_employee_id = new_employee
            candidate_app.converted = True
            candidate_app.save()
            
            messages.success(
                request,
                _("Candidate application has been successfully converted into an employee."),
            )
        except Exception as e:
            messages.error(request, f"An error occurred while creating employee data: {str(e)}")
    else:
        messages.info(request, "An employee with this email already exists")

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@permission_required(perm="recruitment.delete_candidateapplication")
def candidate_application_delete(request, app_id):
    """
    This method is used to delete candidate application
    """
    candidate_app = get_object_or_404(CandidateApplication, id=app_id)
    
    if request.method == "POST":
        try:
            candidate_app.delete()
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'status': 'success',
                    'message': _("Candidate application deleted successfully.")
                })
            else:
                messages.success(request, _("Candidate application deleted successfully."))
                return redirect("candidate-application-view")
        except Exception as e:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'status': 'error',
                    'message': _("Error deleting candidate application: {}").format(str(e))
                }, status=400)
            else:
                messages.error(request, _("Error deleting candidate application: {}").format(str(e)))
                return redirect("candidate-application-view")
    
    # For GET requests, return the delete confirmation modal
    if request.headers.get('HX-Request'):
        context = {
            "candidate_app": candidate_app,
        }
        return render(
            request, 
            "candidate_application/candidate_application_delete_modal.html", 
            context
        )
    else:
        # Fallback for non-AJAX requests
        context = {
            "candidate_app": candidate_app,
        }
        return render(
            request, 
            "candidate_application/candidate_application_delete_form.html", 
            context
        )


@login_required
@permission_required(perm="recruitment.archive_candidateapplication")
def candidate_application_archive(request, app_id):
    """
    This method is used to archive candidate application
    """
    candidate_app = get_object_or_404(CandidateApplication, id=app_id)
    candidate_app.is_active = False
    candidate_app.save()
    messages.success(request, _("Candidate application archived successfully."))
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@permission_required(perm="recruitment.view_candidateapplication")
def candidate_application_export(request):
    """
    This method is used to export candidate application data
    """
    if request.META.get("HTTP_HX_REQUEST"):
        export_column = CandidateApplicationExportForm()
        export_filter = CandidateApplicationFilter()
        content = {
            "export_filter": export_filter,
            "export_column": export_column,
        }
        return render(request, "candidate_application/export_filter.html", context=content)
    return export_data(
        request=request,
        model=CandidateApplication,
        filter_class=CandidateApplicationFilter,
        form_class=CandidateApplicationExportForm,
        file_name="Candidate_Application_export",
    )


@login_required
def recruitment_stage_get_application(request, rec_id):
    """
    This method returns all stages as json for a recruitment
    """
    recruitment_obj = Recruitment.objects.get(id=rec_id)
    all_stages = recruitment_obj.stage_set.all()
    all_stage_json = serializers.serialize("json", all_stages)
    return JsonResponse({"stages": all_stage_json})


# Search and Filter views
@login_required
@permission_required(perm="recruitment.view_candidateapplication")
def candidate_application_search(request):
    """
    This method is used to search candidate applications
    """
    previous_data = request.environ["QUERY_STRING"]
    search_query = request.GET.get("search", "")
    candidate_applications = CandidateApplication.objects.filter(is_active=True)
    
    if search_query:
        candidate_applications = candidate_applications.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(recruitment_id__title__icontains=search_query) |
            Q(stage_id__stage__icontains=search_query)
        )
    
    # Apply filters
    filter_obj = CandidateApplicationFilter(request.GET, queryset=candidate_applications)
    candidate_applications = filter_obj.qs
    
    # Sort and paginate
    candidate_applications = sortby(request, candidate_applications, "orderby")
    candidate_applications = paginator_qry(candidate_applications, request.GET.get("page"))
    
    # Get emails that already exist as users
    mails = list(CandidateApplication.objects.values_list("email", flat=True))
    existing_emails = list(
        User.objects.filter(username__in=mails).values_list("email", flat=True)
    )
    
    # Group by fields for the dropdown
    gp_fields = [
        ("recruitment_id", _("Recruitment")),
        ("stage_id", _("Stage")),
        ("job_position_id", _("Job Position")),
        ("hired", _("Hired")),
        ("canceled", _("Canceled")),
        ("converted", _("Converted")),
        ("is_active", _("Is Active")),
    ]
    
    # Determine template based on view parameter
    template = "candidate_application/candidate_application_card.html"
    if request.GET.get("view") == "list":
        template = "candidate_application/candidate_application_list.html"
    
    context = {
        "candidate_applications": candidate_applications,
        "pd": previous_data,
        "filter_obj": filter_obj,
        "view_type": request.GET.get("view", "card"),
        "existing_emails": existing_emails,
        "gp_fields": gp_fields,
    }
    return render(request, template, context)


@login_required
@permission_required(perm="recruitment.view_candidateapplication")
def candidate_application_filter_view(request):
    """
    This method is used to filter candidate applications
    """
    previous_data = request.environ["QUERY_STRING"]
    
    # Apply filters using the filter object
    candidate_applications = CandidateApplication.objects.filter(is_active=True)
    filter_obj = CandidateApplicationFilter(request.GET, queryset=candidate_applications)
    candidate_applications = filter_obj.qs
    
    # Sort and paginate
    candidate_applications = sortby(request, candidate_applications, "orderby")
    candidate_applications = paginator_qry(candidate_applications, request.GET.get("page"))
    
    # Get emails that already exist as users
    mails = list(CandidateApplication.objects.values_list("email", flat=True))
    existing_emails = list(
        User.objects.filter(username__in=mails).values_list("email", flat=True)
    )
    
    # Group by fields for the dropdown
    gp_fields = [
        ("recruitment_id", _("Recruitment")),
        ("stage_id", _("Stage")),
        ("job_position_id", _("Job Position")),
        ("hired", _("Hired")),
        ("canceled", _("Canceled")),
        ("converted", _("Converted")),
        ("is_active", _("Is Active")),
    ]
    
    # Determine template based on view parameter
    template = "candidate_application/candidate_application_card.html"
    if request.GET.get("view") == "list":
        template = "candidate_application/candidate_application_list.html"
    
    context = {
        "candidate_applications": candidate_applications,
        "pd": previous_data,
        "filter_obj": filter_obj,
        "view_type": request.GET.get("view", "card"),
        "existing_emails": existing_emails,
        "gp_fields": gp_fields,
    }
    return render(request, template, context)


@login_required
def get_job_positions(request):
    """
    AJAX view to get job positions filtered by recruitment
    """
    recruitment_id = request.GET.get('recruitment_id')
    
    if not recruitment_id:
        return JsonResponse({'job_positions': []})
    
    try:
        recruitment = Recruitment.objects.get(id=recruitment_id)
        job_positions = recruitment.open_positions.all().order_by('job_position')
        
        job_positions_data = [
            {
                'id': job_position.id,
                'name': job_position.job_position
            }
            for job_position in job_positions
        ]
        
        return JsonResponse({'job_positions': job_positions_data})
    except Recruitment.DoesNotExist:
        return JsonResponse({'job_positions': []}) 


@login_required
@permission_required(perm="recruitment.add_candidateapplication")
def candidate_application_create_from_pipeline(request):
    """
    This method is used to create candidate application from pipeline context
    with pre-populated recruitment and job position
    """
    # Get stage_id from request
    stage_id = request.GET.get('stage_id')
    
    if not stage_id:
        messages.error(request, _("Stage ID is required."))
        return redirect("candidate-application-view")
    
    try:
        stage = Stage.objects.get(id=stage_id)
        recruitment = stage.recruitment_id
        job_position = recruitment.job_position_id
        
        # If recruitment doesn't have a job position, try to get it from open_positions
        if not job_position and hasattr(recruitment, 'open_positions') and recruitment.open_positions.exists():
            job_position = recruitment.open_positions.first()
            
    except Stage.DoesNotExist:
        messages.error(request, _("Stage not found."))
        return redirect("candidate-application-view")
    
    # Create form with pre-populated context
    form = SimpleCandidateApplicationForm()
    
    # Pre-populate recruitment and job position
    form.fields['recruitment'].initial = recruitment.id
    form.fields['job_position'].initial = job_position.id if job_position else None
    
    # Make recruitment and job position readonly since we're in pipeline context
    form.fields['recruitment'].widget.attrs['readonly'] = 'readonly'
    form.fields['job_position'].widget.attrs['readonly'] = 'readonly'
    form.fields['recruitment'].widget.attrs['class'] = 'oh-input w-100'
    form.fields['job_position'].widget.attrs['class'] = 'oh-input w-100'
    
    if request.method == "POST":
        form = SimpleCandidateApplicationForm(request.POST)
        
        # Pre-populate the form data with recruitment and job position
        if form.is_valid():
            # Override recruitment and job position with pipeline context
            form.cleaned_data['recruitment'] = recruitment
            form.cleaned_data['job_position'] = job_position
        else:
            # If form is invalid, try to fix the recruitment and job position fields
            # and re-validate
            
            if 'recruitment' in form.data:
                try:
                    recruitment_id = form.data.get('recruitment')
                    if recruitment_id:
                        form.cleaned_data = form.cleaned_data or {}
                        form.cleaned_data['recruitment'] = recruitment
                        form.errors.pop('recruitment', None)
                except Exception as e:
                    pass
            
            if 'job_position' in form.data:
                try:
                    job_position_id = form.data.get('job_position')
                    if job_position_id:
                        form.cleaned_data = form.cleaned_data or {}
                        form.cleaned_data['job_position'] = job_position
                        form.errors.pop('job_position', None)
                except Exception as e:
                    pass
            else:
                # If job_position is not in form data, use the one from recruitment
                if job_position:
                    form.cleaned_data = form.cleaned_data or {}
                    form.cleaned_data['job_position'] = job_position
                    form.errors.pop('job_position', None)
            
            # Re-validate the form
            if not form.errors:
                form.cleaned_data['recruitment'] = recruitment
                form.cleaned_data['job_position'] = job_position
        
        # Now process the form if it's valid
        if form.is_valid() or (form.cleaned_data and 'candidates' in form.cleaned_data):
            try:
                created_applications = form.save()
                if created_applications:
                    # Assign candidates to the specific stage
                    for application in created_applications:
                        application.stage_id = stage
                        application.save()
                    
                    success_message = _("Successfully created {} candidate application(s) in {} stage.").format(
                        len(created_applications), stage.stage
                    )
                    return HttpResponse(
                        f'<div class="oh-alert-container"><div class="oh-alert oh-alert--animated oh-alert--success">{success_message}</div><script>$(".oh-modal").removeClass("oh-modal--show"); htmx.ajax("GET", "/recruitment/candidate-stage-component/?stage_id={stage.id}", {{target: "#pipelineStageContainer{stage.id}"}});</script></div>'
                    )
                else:
                    warning_message = _("No new applications were created. Applications may already exist for the selected candidates.")
                    return HttpResponse(
                        f'<div class="oh-alert-container"><div class="oh-alert oh-alert--animated oh-alert--warning">{warning_message}</div><script>$(".oh-modal").removeClass("oh-modal--show");</script></div>'
                    )
            except Exception as e:
                error_message = _("Error creating candidate applications: {}").format(str(e))
                import traceback
                return HttpResponse(
                    f'<div class="oh-alert-container"><div class="oh-alert oh-alert--animated oh-alert--danger">{error_message}</div><script>$(".oh-modal").removeClass("oh-modal--show");</script></div>'
                )
        else:
            # Form is invalid, return the form with errors
            context = {
                "form": form,
                "stage": stage,
                "recruitment": recruitment,
                "job_position": job_position,
            }
            return render(
                request,
                "candidate_application/candidate_application_create_from_pipeline_modal.html",
                context,
            )
    
    # GET request - return the form
    context = {
        "form": form,
        "stage": stage,
        "recruitment": recruitment,
        "job_position": job_position,
    }
    return render(
        request,
        "candidate_application/candidate_application_create_from_pipeline_modal.html",
        context,
    ) 