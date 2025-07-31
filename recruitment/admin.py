"""
admin.py

This page is used to register the model with admins site.
"""

from django.contrib import admin

from recruitment.models import (
    Candidate,
    CandidateRating,
    Recruitment,
    RecruitmentSurvey,
    RecruitmentSurveyAnswer,
    Skill,
    TechnicalSkill,
    NonTechnicalSkill,
    SkillZone,
    Stage,
    CandidateApplication,
    InterviewScheduleApplication,
    StageNoteApplication,
    RecruitmentSurveyAnswerApplication,
    CandidateWorkExperience,
    CandidateWorkProject,
    CandidateEducation,
    CandidateCertification,
    CandidateSkill,
    CandidateApplicationSkillRating
)

# Register your models here.


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    """
    Admin interface for Stage model
    """
    list_display = [
        "stage",
        "recruitment_id",
        "stage_type",
        "sequence",
        "get_stage_managers",
        "get_stage_interviewers",
    ]
    list_filter = [
        "stage_type",
        "recruitment_id",
        "recruitment_id__company_id",
    ]
    search_fields = [
        "stage",
        "recruitment_id__title",
    ]
    ordering = ["recruitment_id", "sequence"]
    filter_horizontal = ["stage_managers", "stage_interviewers"]
    
    def get_stage_managers(self, obj):
        return ", ".join([manager.get_full_name() for manager in obj.stage_managers.all()])
    get_stage_managers.short_description = "Stage Managers"
    
    def get_stage_interviewers(self, obj):
        return ", ".join([interviewer.get_full_name() for interviewer in obj.stage_interviewers.all()])
    get_stage_interviewers.short_description = "Stage Interviewers"
@admin.register(Recruitment)
class RecruitmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Recruitment model
    """
    list_display = [
        "title",
        "job_position_id",
        "employment_type",
        "work_location",
        "vacancy",
        "is_published",
        "closed",
        "start_date",
        "end_date",
    ]
    list_filter = [
        "employment_type",
        "remote_policy",
        "required_education_level",
        "is_published",
        "closed",
        "start_date",
        "company_id",
    ]
    search_fields = [
        "title",
        "job_summary",
        "work_location",
        "job_position_id__job_position",
    ]
    ordering = ["-start_date", "title"]
    readonly_fields = []
    
    fieldsets = [
        ("Basic Information", {
            "fields": [
                "title", "job_position_id", "open_positions", "vacancy"
            ]
        }),
        ("Job Details", {
            "fields": [
                "employment_type", "work_location", "remote_policy",
                "salary_min", "salary_max", "salary_currency"
            ]
        }),
        ("Requirements", {
            "fields": [
                "min_experience_years", "max_experience_years", "required_education_level",
                "technical_skills", "non_technical_skills"
            ]
        }),
        ("Job Description", {
            "fields": [
                "job_summary", "key_responsibilities", "preferred_qualifications"
            ]
        }),
        ("Timeline", {
            "fields": [
                "start_date", "end_date", "application_deadline"
            ]
        }),
        ("Recruitment Management", {
            "fields": [
                "recruitment_managers", "default_stage_manager"
            ]
        }),
        ("Interviewer Assignments", {
            "fields": [
                "l1_interviewer", "l2_interviewer", "l3_interviewer"
            ]
        }),
        ("Settings", {
            "fields": [
                "is_published", "closed", "is_event_based",
                "survey_templates"
            ]
        }),

        ("Optional Settings", {
            "fields": [
                "optional_profile_image", "optional_resume"
            ]
        }),
    ]
admin.site.register(Candidate)
admin.site.register(RecruitmentSurveyAnswer)
admin.site.register(RecruitmentSurvey)
admin.site.register(CandidateRating)
admin.site.register(Skill)
admin.site.register(TechnicalSkill)
admin.site.register(NonTechnicalSkill)
admin.site.register(SkillZone)



# CandidateApplication Admin

@admin.register(CandidateApplication)
class CandidateApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface for CandidateApplication model
    """
    list_display = [
        "name",
        "email", 
        "recruitment_id",
        "job_position_id",
        "stage_id",
        "hired",
        "canceled",
        "converted",
        "last_updated",
        "is_active",
    ]
    list_filter = [
        "recruitment_id",
        "job_position_id", 
        "stage_id",
        "hired",
        "canceled",
        "converted",
        "gender",
        "source",
        "offer_letter_status",
        "is_active",
        "recruitment_id__company_id",
    ]
    search_fields = [
        "name",
        "email",
        "mobile",
        "recruitment_id__title",
        "job_position_id__job_position",
    ]
    ordering = ["-last_updated", "name"]
    readonly_fields = [
        "hired_date",
        "probation_end", 
        "offer_letter_status",
        "last_updated",
    ]
    
    fieldsets = [
        (
            "Personal Information",
            {
                "fields": [
                    "name",
                    "email",
                    "mobile",
                    "gender",
                    "dob",
                    "profile",
                    "portfolio",
                ]
            },
        ),
        (
            "Recruitment Information", 
            {
                "fields": [
                    "recruitment_id",
                    "job_position_id",
                    "stage_id",
                    "source",
                    "referral",
                ]
            },
        ),
        (
            "Documents",
            {
                "fields": [
                    "resume",
                ]
            },
        ),
        (
            "Address Information",
            {
                "fields": [
                    "address",
                    "country",
                    "state", 
                    "city",
                    "zip",
                ]
            },
        ),
        (
            "Status & Dates",
            {
                "fields": [
                    "hired",
                    "canceled",
                    "converted",
                    "start_onboard",
                    "schedule_date",
                    "joining_date",
                    "hired_date",
                    "probation_end",
                    "offer_letter_status",
                    "last_updated",
                ]
            },
        ),
        (
            "Employee Conversion",
            {
                "fields": [
                    "converted_employee_id",
                ]
            },
        ),
        (
            "System Fields",
            {
                "fields": [
                    "sequence",
                    "is_active",
                ],
                "classes": ["collapse"],
            },
        ),
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "recruitment_id",
            "job_position_id", 
            "stage_id",
            "converted_employee_id",
            "referral",
        )


@admin.register(InterviewScheduleApplication)
class InterviewScheduleApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface for InterviewScheduleApplication model
    """
    list_display = [
        "candidate_application_id",
        "interview_date",
        "interview_start_time", 
        "completed",
        "get_interviewers",
    ]
    list_filter = [
        "interview_date",
        "completed",
        "candidate_application_id__recruitment_id",
        "candidate_application_id__stage_id",
    ]
    search_fields = [
        "candidate_application_id__name",
        "candidate_application_id__email",
        "description",
    ]
    ordering = ["-interview_date", "-interview_start_time"]
    
    def get_interviewers(self, obj):
        """Display list of interviewers"""
        return ", ".join([emp.get_full_name() for emp in obj.employee_id.all()])
    get_interviewers.short_description = "Interviewers"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "candidate_application_id",
        ).prefetch_related("employee_id")


@admin.register(StageNoteApplication) 
class StageNoteApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface for StageNoteApplication model
    """
    list_display = [
        "candidate_application_id",
        "stage_id",
        "description_preview",
        "updated_by",
        "candidate_can_view",
        "created_at",
    ]
    list_filter = [
        "stage_id",
        "candidate_can_view",
        "candidate_application_id__recruitment_id",
        "updated_by",
    ]
    search_fields = [
        "candidate_application_id__name",
        "candidate_application_id__email", 
        "description",
    ]
    ordering = ["-created_at"]
    readonly_fields = ["created_at"]
    
    def description_preview(self, obj):
        """Show preview of description"""
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_preview.short_description = "Description"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "candidate_application_id",
            "stage_id",
            "updated_by",
        )


@admin.register(RecruitmentSurveyAnswerApplication)
class RecruitmentSurveyAnswerApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface for RecruitmentSurveyAnswerApplication model
    """
    list_display = [
        "candidate_application_id",
        "recruitment_id", 
        "job_position_id",
        "has_attachment",
        "created_at",
    ]
    list_filter = [
        "recruitment_id",
        "job_position_id",
        "candidate_application_id__stage_id",
    ]
    search_fields = [
        "candidate_application_id__name",
        "candidate_application_id__email",
    ]
    ordering = ["-created_at"]
    readonly_fields = ["answer_json", "created_at"]
    
    def has_attachment(self, obj):
        """Check if survey answer has attachment"""
        return bool(obj.attachment)
    has_attachment.boolean = True
    has_attachment.short_description = "Has Attachment"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "candidate_application_id",
            "recruitment_id",
            "job_position_id",
        )


@admin.register(CandidateWorkExperience)
class CandidateWorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job_title', 'company_name', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current', 'employment_type', 'start_date']
    search_fields = ['candidate__name', 'job_title', 'company_name']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']


@admin.register(CandidateWorkProject)
class CandidateWorkProjectAdmin(admin.ModelAdmin):
    list_display = ['work_experience', 'project_name', 'role', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current', 'start_date']
    search_fields = ['project_name', 'work_experience__candidate__name']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']


@admin.register(CandidateEducation)
class CandidateEducationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'degree_name', 'institution_name', 'field_of_study', 'graduation_date', 'is_current']
    list_filter = ['is_current', 'graduation_date']
    search_fields = ['candidate__name', 'degree_name', 'institution_name', 'field_of_study']
    date_hierarchy = 'graduation_date'
    ordering = ['-graduation_date']


@admin.register(CandidateCertification)
class CandidateCertificationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'certification_name', 'issuing_organization', 'issue_date', 'expiry_date', 'is_current']
    list_filter = ['is_current', 'issue_date', 'expiry_date']
    search_fields = ['candidate__name', 'certification_name', 'issuing_organization']
    date_hierarchy = 'issue_date'
    ordering = ['-issue_date']


@admin.register(CandidateSkill)
class CandidateSkillAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'skill_name', 'skill_category', 'proficiency_level', 'years_of_experience', 'is_highlighted']
    list_filter = ['skill_category', 'proficiency_level', 'is_highlighted']
    search_fields = ['candidate__name', 'skill_name']
    ordering = ['skill_category', 'skill_name']


@admin.register(CandidateApplicationSkillRating)
class CandidateApplicationSkillRatingAdmin(admin.ModelAdmin):
    list_display = ['candidate_application', 'stage', 'skill_name', 'skill_category', 'rating', 'employee', 'rated_on']
    list_filter = ['skill_category', 'rating', 'employee', 'rated_on', 'stage']
    search_fields = ['candidate_application__name', 'skill_name', 'employee__user__username', 'stage__stage']
    ordering = ['-rated_on', 'candidate_application__name']
    readonly_fields = ['rated_on']
    date_hierarchy = 'rated_on'
    list_select_related = ['candidate_application', 'stage', 'employee']
