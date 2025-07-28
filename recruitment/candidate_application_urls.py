"""
candidate_application_urls.py

This module contains URL patterns for CandidateApplication views.
These URLs provide parallel functionality to existing candidate URLs
but for the new CandidateApplication junction model.
"""

from django.urls import path

from recruitment.forms import (
    CandidateApplicationCreationForm,
    CandidateApplicationUpdateForm,
    InterviewScheduleApplicationForm,
    StageNoteApplicationForm,
)
from recruitment.models import CandidateApplication, InterviewScheduleApplication
from recruitment.views import candidate_application_views

# URL patterns for CandidateApplication
candidate_application_urlpatterns = [
    # Main CRUD operations
    path(
        "candidate-application-create/",
        candidate_application_views.candidate_application_create,
        name="candidate-application-create",
    ),
    path(
        "candidate-application-view/",
        candidate_application_views.candidate_application_view,
        name="candidate-application-view",
    ),
    path(
        "candidate-application-view/<int:app_id>/",
        candidate_application_views.candidate_application_view_individual,
        name="candidate-application-view-individual",
    ),
    path(
        "candidate-application-update/<int:app_id>/",
        candidate_application_views.candidate_application_update,
        name="candidate-application-update",
    ),
    path(
        "candidate-application-delete/<int:app_id>/",
        candidate_application_views.candidate_application_delete,
        name="candidate-application-delete",
    ),
    path(
        "candidate-application-archive/<int:app_id>/",
        candidate_application_views.candidate_application_archive,
        name="candidate-application-archive",
    ),
    
    # Pipeline and stage management
    path(
        "candidate-application-pipeline/",
        candidate_application_views.candidate_application_pipeline,
        name="candidate-application-pipeline",
    ),
    path(
        "candidate-application-stage-update/<int:app_id>/",
        candidate_application_views.candidate_application_stage_update,
        name="candidate-application-stage-update",
    ),
    
    # Notes management
    path(
        "add-note-application/<int:app_id>/",
        candidate_application_views.add_note_application,
        name="add-note-application",
    ),
    
    # Interview scheduling
    path(
        "interview-schedule-application/<int:app_id>/",
        candidate_application_views.interview_schedule_application,
        name="interview-schedule-application",
    ),
    path(
        "interview-view-application/",
        candidate_application_views.interview_view_application,
        name="interview-view-application",
    ),
    
    # Employee conversion
    path(
        "candidate-application-conversion/<int:app_id>/",
        candidate_application_views.candidate_application_conversion,
        name="candidate-application-conversion",
    ),
    
    # Data export and utilities
    path(
        "candidate-application-export/",
        candidate_application_views.candidate_application_export,
        name="candidate-application-export",
    ),
    path(
        "recruitment-stage-get-application/<int:rec_id>/",
        candidate_application_views.recruitment_stage_get_application,
        name="recruitment-stage-get-application",
    ),
    
    # Search and filtering
    path(
        "candidate-application-search/",
        candidate_application_views.candidate_application_search,
        name="candidate-application-search",
    ),
    path(
        "candidate-application-filter-view/",
        candidate_application_views.candidate_application_filter_view,
        name="candidate-application-filter-view",
    ),
] 