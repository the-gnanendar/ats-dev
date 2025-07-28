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
from base.methods import get_pagination, sortby
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
)
from recruitment.models import (
    CandidateApplication,
    InterviewScheduleApplication,
    Recruitment,
    Stage,
    StageNoteApplication,
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
        if form.is_valid():
            try:
                created_applications = form.save()
                if created_applications:
                    messages.success(
                        request, 
                        _("Successfully created {} candidate application(s).").format(len(created_applications))
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
    
    context = {
        "candidate_applications": candidate_applications,
        "pd": previous_data,
        "filter_obj": filter_obj,
        "requests_ids": requests_ids,
        "view_type": view_type,
        "gp_fields": CandidateApplicationFilter._meta.fields,
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
    form = CandidateApplicationUpdateForm(instance=candidate_app)
    
    if request.method == "POST":
        form = CandidateApplicationUpdateForm(
            request.POST, request.FILES, instance=candidate_app
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
        "candidate_application/candidate_application_update_form.html", 
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
        candidate_app.delete()
        messages.success(request, _("Candidate application deleted successfully."))
        return redirect("candidate-application-view")
    
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
    selected_columns = request.GET.getlist("selected_fields")
    candidate_applications = CandidateApplicationFilter(
        request.GET, 
        queryset=CandidateApplication.objects.filter(is_active=True)
    ).qs
    
    # Export logic here - can be CSV, Excel, etc.
    # For now, just return the data as JSON
    data = []
    for app in candidate_applications:
        app_data = {
            "name": app.name,
            "email": app.email,
            "mobile": app.mobile,
            "recruitment": app.recruitment_id.title if app.recruitment_id else "",
            "job_position": app.job_position_id.job_position if app.job_position_id else "",
            "stage": app.stage_id.stage if app.stage_id else "",
            "hired": app.hired,
            "canceled": app.canceled,
        }
        data.append(app_data)
    
    return JsonResponse({"data": data})


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
    search_query = request.GET.get("search", "")
    candidate_applications = CandidateApplication.objects.filter(is_active=True)
    
    if search_query:
        candidate_applications = candidate_applications.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(recruitment_id__title__icontains=search_query) |
            Q(stage_id__stage__icontains=search_query)
        )
    
    context = {
        "candidate_applications": candidate_applications,
        "search_query": search_query,
    }
    return render(request, "candidate_application/search_results.html", context)


@login_required
@permission_required(perm="recruitment.view_candidateapplication")
def candidate_application_filter_view(request):
    """
    This method is used to filter candidate applications
    """
    candidate_applications = CandidateApplication.objects.filter(is_active=True)
    filter_obj = CandidateApplicationFilter(request.GET, queryset=candidate_applications)
    
    context = {
        "candidate_applications": filter_obj.qs,
        "filter_obj": filter_obj,
    }
    return render(request, "candidate_application/filter_view.html", context) 