"""
models.py

This module is used to register models for recruitment app

"""

import json
import os
import re
from datetime import date
from uuid import uuid4

import django
import requests
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from base.horilla_company_manager import HorillaCompanyManager
from base.models import Company, JobPosition
from employee.models import Employee
from horilla.models import HorillaModel
from horilla_audit.methods import get_diff
from horilla_audit.models import HorillaAuditInfo, HorillaAuditLog
from horilla_views.cbv_methods import render_template

# Create your models here.


def validate_mobile(value):
    """
    This method is used to validate the mobile number using regular expression
    """
    pattern = r"^\+[0-9 ]+$|^[0-9 ]+$"

    if re.match(pattern, value) is None:
        if "+" in value:
            raise forms.ValidationError(
                "Invalid input: Plus symbol (+) should only appear at the beginning \
                    or no other characters allowed."
            )
        raise forms.ValidationError(
            "Invalid input: Only digits and spaces are allowed."
        )


def validate_pdf(value):
    """
    This method is used to validate pdf
    """
    ext = os.path.splitext(value.name)[1]  # Get file extension
    if ext.lower() != ".pdf":
        raise ValidationError(_("File must be a PDF."))


def validate_image(value):
    """
    This method is used to validate the image
    """
    return value


def candidate_photo_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{instance.name.replace(' ', '_')}_{filename}_{uuid4()}.{ext}"
    return os.path.join("recruitment/profile/", filename)


class SurveyTemplate(HorillaModel):
    """
    SurveyTemplate Model
    """

    title = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    is_general_template = models.BooleanField(default=False, editable=False)
    company_id = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Company"),
    )
    objects = HorillaCompanyManager("company_id")

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = _("Survey Template")
        verbose_name_plural = _("Survey Templates")


class Skill(HorillaModel):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        title = self.title
        self.title = title.capitalize()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")


class TechnicalSkill(HorillaModel):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        title = self.title
        self.title = title.capitalize()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Technical Skill")
        verbose_name_plural = _("Technical Skills")


class NonTechnicalSkill(HorillaModel):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        title = self.title
        self.title = title.capitalize()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Non-Technical Skill")
        verbose_name_plural = _("Non-Technical Skills")


class Recruitment(HorillaModel):
    """
    Recruitment model
    """

    title = models.CharField(
        max_length=50, null=True, blank=True, verbose_name=_("Title")
    )

    is_event_based = models.BooleanField(
        default=False,
        help_text=_("To start recruitment for multiple job positions"),
    )
    closed = models.BooleanField(
        default=False,
        help_text=_(
            "To close the recruitment, If closed then not visible on pipeline view."
        ),
        verbose_name=_("Closed"),
    )
    is_published = models.BooleanField(
        default=True,
        help_text=_(
            "To publish a recruitment in website, if false then it \
            will not appear on open recruitment page."
        ),
        verbose_name=_("Is Published"),
    )
    open_positions = models.ManyToManyField(
        JobPosition,
        related_name="open_positions",
        blank=True,
        verbose_name=_("Job Position"),
    )
    job_position_id = models.ForeignKey(
        JobPosition,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_constraint=False,
        related_name="recruitment",
        verbose_name=_("Job Position"),
        editable=False,
    )
    vacancy = models.IntegerField(default=0, null=True, verbose_name=_("Vacancy"))
    recruitment_managers = models.ManyToManyField(Employee, verbose_name=_("Managers"))
    
    # Default Stage Manager for all stages
    default_stage_manager = models.ManyToManyField(
        Employee, 
        verbose_name=_("Default Stage Manager"),
        help_text=_("This manager will be assigned to all stages by default"),
        related_name="default_stage_manager_recruitments",
        blank=True
    )
    
    # Interviewer assignments for specific stages
    l1_interviewer = models.ManyToManyField(
        Employee,
        verbose_name=_("L1 Interviewer"),
        help_text=_("Interviewers for L1 Interview stage"),
        related_name="l1_interviewer_recruitments",
        blank=True
    )
    l2_interviewer = models.ManyToManyField(
        Employee,
        verbose_name=_("L2 Interviewer"),
        help_text=_("Interviewers for L2 Interview stage"),
        related_name="l2_interviewer_recruitments",
        blank=True
    )
    l3_interviewer = models.ManyToManyField(
        Employee,
        verbose_name=_("L3 Interviewer"),
        help_text=_("Interviewers for L3 Interview stage"),
        related_name="l3_interviewer_recruitments",
        blank=True
    )
    
    survey_templates = models.ManyToManyField(
        SurveyTemplate, blank=True, verbose_name=_("Survey Templates")
    )
    company_id = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Company"),
    )
    start_date = models.DateField(
        default=django.utils.timezone.now, verbose_name=_("Start Date")
    )
    end_date = models.DateField(blank=True, null=True, verbose_name=_("End Date"))
    technical_skills = models.ManyToManyField(TechnicalSkill, blank=True, verbose_name=_("Technical Skills"))
    non_technical_skills = models.ManyToManyField(NonTechnicalSkill, blank=True, verbose_name=_("Non-Technical Skills"))
    linkedin_account_id = models.ForeignKey(
        "recruitment.LinkedInAccount",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("LinkedIn Account"),
    )
    linkedin_post_id = models.CharField(max_length=150, null=True, blank=True)
    publish_in_linkedin = models.BooleanField(
        default=True,
        help_text=_(
            "To publish a recruitment in Linkedin, if active is false then it \
            will not post on LinkedIn."
        ),
        verbose_name=_("Post on LinkedIn"),
    )
    objects = HorillaCompanyManager()
    default = models.manager.Manager()
    optional_profile_image = models.BooleanField(
        default=False,
        help_text=_("Profile image not mandatory for candidate creation"),
        verbose_name=_("Optional Profile Image"),
    )
    optional_resume = models.BooleanField(
        default=False,
        help_text=_("Resume not mandatory for candidate creation"),
        verbose_name=_("Optional Resume"),
    )
    
    # Salary Range
    salary_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Minimum Salary"),
        help_text=_("Minimum annual salary for this position")
    )
    salary_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Salary"),
        help_text=_("Maximum annual salary for this position")
    )
    salary_currency = models.CharField(
        max_length=3,
        default="USD",
        verbose_name=_("Salary Currency"),
        help_text=_("Currency for salary range (e.g., USD, EUR, GBP)")
    )
    
    # Employment Type
    employment_type_choices = [
        ("full_time", _("Full Time")),
        ("part_time", _("Part Time")),
        ("contract", _("Contract")),
        ("internship", _("Internship")),
        ("freelance", _("Freelance")),
        ("remote", _("Remote")),
        ("hybrid", _("Hybrid")),
    ]
    employment_type = models.CharField(
        max_length=20,
        choices=employment_type_choices,
        default="full_time",
        verbose_name=_("Employment Type"),
        help_text=_("Type of employment for this position")
    )
    
    # Location Details
    work_location = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Work Location"),
        help_text=_("City, State, or specific office location")
    )
    remote_policy = models.CharField(
        max_length=20,
        choices=[
            ("on_site", _("On-Site Only")),
            ("remote", _("Fully Remote")),
            ("hybrid", _("Hybrid (Remote + Office)")),
            ("flexible", _("Flexible")),
        ],
        default="on_site",
        verbose_name=_("Remote Work Policy"),
        help_text=_("Remote work policy for this position")
    )
    
    # Experience Requirements
    min_experience_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Minimum Years of Experience"),
        help_text=_("Minimum years of relevant experience required")
    )
    max_experience_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Maximum Years of Experience"),
        help_text=_("Maximum years of experience (optional)")
    )
    required_education_level = models.CharField(
        max_length=20,
        choices=[
            ("high_school", _("High School")),
            ("associate", _("Associate Degree")),
            ("bachelor", _("Bachelor's Degree")),
            ("master", _("Master's Degree")),
            ("phd", _("PhD")),
            ("none", _("No Degree Required")),
        ],
        default="bachelor",
        verbose_name=_("Required Education Level"),
        help_text=_("Minimum education level required")
    )
    
    # Application Deadline
    application_deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Application Deadline"),
        help_text=_("Last date to submit applications")
    )
    
    # Job Description Sections
    job_summary = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Job Summary"),
        help_text=_("Brief overview of the role and its impact")
    )
    key_responsibilities = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Key Responsibilities"),
        help_text=_("Main duties and responsibilities for this role")
    )
    preferred_qualifications = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Preferred Qualifications"),
        help_text=_("Additional qualifications that would be beneficial")
    )
    
    xss_exempt_fields = ["job_summary", "key_responsibilities", "preferred_qualifications"]  # 807

    class Meta:
        """
        Meta class to add the additional info
        """

        unique_together = [
            (
                "job_position_id",
                "start_date",
            ),
            ("job_position_id", "start_date", "company_id"),
        ]
        permissions = (("archive_recruitment", "Archive Recruitment"),)
        verbose_name = _("Recruitment")
        verbose_name_plural = _("Recruitments")

    def total_hires(self):
        """
        This method is used to get the count of
        hired candidates
        """
        return self.candidate.filter(hired=True).count()

    def __str__(self):
        title = (
            f"{self.job_position_id.job_position} {self.start_date}"
            if self.title is None and self.job_position_id
            else self.title
        )

        if not self.is_event_based and self.job_position_id is not None:
            self.open_positions.add(self.job_position_id)

        return title

    def clean(self):
        if self.title is None:
            raise ValidationError({"title": _("This field is required")})
        if self.is_published:
            if self.vacancy <= 0:
                raise ValidationError(
                    _(
                        "Vacancy must be greater than zero if the recruitment is publishing."
                    )
                )

        if self.end_date is not None and (
            self.start_date is not None and self.start_date > self.end_date
        ):
            raise ValidationError(
                {"end_date": _("End date cannot be less than start date.")}
            )
        return super().clean()

    def save(self, *args, **kwargs):
        if not self.publish_in_linkedin:
            self.linkedin_account_id = None
            self.linkedin_post_id = None
        super().save(*args, **kwargs)  # Save the Recruitment instance first
        if self.is_event_based and self.open_positions is None:
            raise ValidationError({"open_positions": _("This field is required")})

    def ordered_stages(self):
        """
        This method will returns all the stage respectively to the ascending order of stages
        """
        return self.stage_set.order_by("sequence")

    def is_vacancy_filled(self):
        """
        This method is used to check wether the vaccancy for the recruitment is completed or not
        """
        selected_stage = Stage.objects.filter(
            recruitment_id=self, stage_type="selected"
        ).first()
        if selected_stage:
            selected_candidate = selected_stage.candidate_set.all().exclude(canceled=True)
            if len(selected_candidate) >= self.vacancy:
                return True
    
    def create_default_stages(self):
        """
        This method creates default stages for the recruitment
        """
        default_stages = [
            {"stage": "Sourced", "stage_type": "sourced", "sequence": 1},
            {"stage": "Shortlisted", "stage_type": "shortlisted", "sequence": 2},
            {"stage": "L1 Interview", "stage_type": "l1_interview", "sequence": 3},
            {"stage": "L2 Interview", "stage_type": "l2_interview", "sequence": 4},
            {"stage": "L3 Interview", "stage_type": "l3_interview", "sequence": 5},
            {"stage": "Test", "stage_type": "test", "sequence": 6},
            {"stage": "Selected", "stage_type": "selected", "sequence": 7},
            {"stage": "Rejected", "stage_type": "rejected", "sequence": 8},
            {"stage": "On Hold", "stage_type": "on-hold", "sequence": 9},
        ]
        
        for stage_data in default_stages:
            stage, created = Stage.objects.get_or_create(
                recruitment_id=self,
                stage=stage_data["stage"],
                defaults={
                    "stage_type": stage_data["stage_type"],
                    "sequence": stage_data["sequence"],
                }
            )
            
            # Assign default stage manager to all stages
            if self.default_stage_manager.exists():
                stage.stage_managers.set(self.default_stage_manager.all())
            
            # Assign specific interviewers to interview stages
            if stage_data["stage_type"] == "l1_interview" and self.l1_interviewer.exists():
                stage.stage_interviewers.set(self.l1_interviewer.all())
            elif stage_data["stage_type"] == "l2_interview" and self.l2_interviewer.exists():
                stage.stage_interviewers.set(self.l2_interviewer.all())
            elif stage_data["stage_type"] == "l3_interview" and self.l3_interviewer.exists():
                stage.stage_interviewers.set(self.l3_interviewer.all())
            
            stage.save()


class Stage(HorillaModel):
    """
    Stage model
    """

    stage_types = [
        ("sourced", _("Sourced")),
        ("shortlisted", _("Shortlisted")),
        ("l1_interview", _("L1 Interview")),
        ("l2_interview", _("L2 Interview")),
        ("l3_interview", _("L3 Interview")),
        ("test", _("Test")),
        ("interview", _("Interview")),
        ("selected", _("Selected")),
        ("rejected", _("Rejected")),
        ("on-hold", _("On Hold")),
        ("cancelled", _("Cancelled")),
    ]
    recruitment_id = models.ForeignKey(
        Recruitment,
        on_delete=models.CASCADE,
        related_name="stage_set",
        verbose_name=_("Recruitment"),
    )
    stage_managers = models.ManyToManyField(Employee, verbose_name=_("Stage Managers"))
    stage_interviewers = models.ManyToManyField(
        Employee, 
        verbose_name=_("Stage Interviewers"),
        related_name="stage_interviewers",
        blank=True
    )
    stage = models.CharField(max_length=50, verbose_name=_("Stage"))
    stage_type = models.CharField(
        max_length=20,
        choices=stage_types,
        default="sourced",
        verbose_name=_("Stage Type"),
    )
    sequence = models.IntegerField(null=True, default=0)
    objects = HorillaCompanyManager(related_company_field="recruitment_id__company_id")

    def __str__(self):
        return f"{self.stage}"

    class Meta:
        """
        Meta class to add the additional info
        """

        permissions = (("archive_Stage", "Archive Stage"),)
        unique_together = ["recruitment_id", "stage"]
        ordering = ["sequence"]
        verbose_name = _("Stage")
        verbose_name_plural = _("Stages")

    def __str__(self):
        return f"{self.stage} - ({self.recruitment_id.title})"

    def active_candidates(self):
        """
        This method is used to get all the active candidate like related objects
        """
        return {
            "all": Candidate.objects.filter(
                stage_id=self, canceled=False, is_active=True
            )
        }


class Candidate(HorillaModel):
    """
    Candidate model - recruitment-agnostic candidate profile
    """

    choices = [("male", _("Male")), ("female", _("Female")), ("other", _("Other"))]
    source_choices = [
        ("application", _("Application Form")),
        ("software", _("Inside software")),
        ("referral", _("Employee Referral")),
        ("linkedin", _("LinkedIn")),
        ("website", _("Company Website")),
        ("other", _("Other")),
    ]
    
    # Core Identity Fields
    name = models.CharField(max_length=100, null=True, verbose_name=_("Name"))
    email = models.EmailField(max_length=254, unique=True, verbose_name=_("Email"))
    mobile = models.CharField(
        max_length=15,
        blank=True,
        validators=[validate_mobile],
        verbose_name=_("Mobile"),
    )
    
    # Profile Information
    profile = models.ImageField(upload_to=candidate_photo_upload_path, null=True)
    portfolio = models.URLField(max_length=200, blank=True)
    resume = models.FileField(
        upload_to="recruitment/resume",
        validators=[validate_pdf],
    )
    
    # Personal Information
    address = models.TextField(
        null=True, blank=True, verbose_name=_("Address"), max_length=255
    )
    country = models.CharField(
        max_length=30, null=True, blank=True, verbose_name=_("Country")
    )
    dob = models.DateField(null=True, blank=True, verbose_name=_("Date of Birth"))
    state = models.CharField(
        max_length=30, null=True, blank=True, verbose_name=_("State")
    )
    city = models.CharField(
        max_length=30, null=True, blank=True, verbose_name=_("City")
    )
    zip = models.CharField(
        max_length=30, null=True, blank=True, verbose_name=_("Zip Code")
    )
    gender = models.CharField(
        max_length=15,
        choices=choices,
        null=True,
        default="male",
        verbose_name=_("Gender"),
    )
    
    # Source Information
    source = models.CharField(
        max_length=20,
        choices=source_choices,
        null=True,
        blank=True,
        verbose_name=_("Source"),
    )
    referral = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="candidate_referral",
        verbose_name=_("Referral"),
    )
    
    # Employee Conversion (General)
    converted_employee_id = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="candidate_get",
        verbose_name=_("Employee"),
    )
    converted = models.BooleanField(default=False, verbose_name=_("Converted"))
    
    # Audit and Metadata
    history = HorillaAuditLog(
        related_name="history_set",
        bases=[HorillaAuditInfo],
    )
    last_updated = models.DateField(null=True, auto_now=True)
    
    # Manager and settings
    objects = models.Manager()  # Use default manager since no company relationship
    converted_employee_id.exclude_from_automation = True

    def __str__(self):
        return f"{self.name}"

    def is_offer_rejected(self):
        """
        Is offer rejected checking method
        """
        first = RejectedCandidate.objects.filter(candidate_id=self).first()
        if first:
            return first.reject_reason_id.count() > 0
        return first

    def get_full_name(self):
        """
        Method will return employee full name
        """
        return str(self.name)

    def get_avatar(self):
        """
        Method will rerun the api to the avatar or path to the profile image
        """
        url = (
            f"https://ui-avatars.com/api/?name={self.get_full_name()}&background=random"
        )
        if self.profile:
            full_filename = self.profile.name

            if default_storage.exists(full_filename):
                url = self.profile.url

        return url

    def get_company(self):
        """
        This method is used to return the company - now based on employee conversion
        """
        if self.converted_employee_id:
            return getattr(
                getattr(self.converted_employee_id, "employee_work_info", None),
                "company_id",
                None,
            )
        return None

    def get_email(self):
        """
        Return email
        """
        return self.email

    def get_mail(self):
        """ """
        return self.get_email()

    def phone(self):
        return self.mobile

    def tracking(self):
        """
        This method is used to return the tracked history of the instance
        """
        return get_diff(self)

    def get_last_sent_mail(self):
        """
        This method is used to get last send mail
        """
        from base.models import EmailLog

        return (
            EmailLog.objects.filter(to__icontains=self.email)
            .order_by("-created_at")
            .first()
        )

    def get_interview(self):
        """
        This method returns interview information for this candidate across all their applications
        """
        interviews = InterviewSchedule.objects.filter(candidate_id=self.id)
        if interviews:
            interview_info = "<table>"
            interview_info += "<tr><th>Sl No.</th><th>Date</th><th>Time</th><th>Is Completed</th></tr>"
            for index, interview in enumerate(interviews, start=1):
                interview_info += f"<tr><td>{index}</td>"
                interview_info += (
                    f"<td class='dateformat_changer'>{interview.interview_date}</td>"
                )
                interview_info += (
                    f"<td class='timeformat_changer'>{interview.interview_time}</td>"
                )
                interview_info += (
                    f"<td>{'Yes' if interview.completed else 'No'}</td></tr>"
                )
            interview_info += "</table>"
            return interview_info
        else:
            return ""

    def save(self, *args, **kwargs):
        # Ensure employee uniqueness for candidate conversion
        if (
            self.converted_employee_id
            and Candidate.objects.filter(
                converted_employee_id=self.converted_employee_id
            )
            .exclude(id=self.id)
            .exists()
        ):
            raise ValidationError(_("Employee is unique for candidate"))

        super().save(*args, **kwargs)

    class Meta:
        """
        Meta class to add the additional info
        """
        permissions = (
            ("view_history", "View Candidate History"),
            ("archive_candidate", "Archive Candidate"),
        )
        ordering = ["name"]
        verbose_name = _("Candidate")
        verbose_name_plural = _("Candidates")


class RejectReason(HorillaModel):
    """
    RejectReason
    """

    title = models.CharField(
        max_length=50,
    )
    description = models.TextField(null=True, blank=True, max_length=255)
    company_id = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Company"),
    )
    objects = HorillaCompanyManager()

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = _("Reject Reason")
        verbose_name_plural = _("Reject Reasons")


class RejectedCandidate(HorillaModel):
    """
    RejectedCandidate
    """

    candidate_id = models.OneToOneField(
        Candidate,
        on_delete=models.PROTECT,
        verbose_name="Candidate",
        related_name="rejected_candidate",
    )
    reject_reason_id = models.ManyToManyField(
        RejectReason, verbose_name="Reject reason", blank=True
    )
    description = models.TextField(max_length=255)
    objects = HorillaCompanyManager(
        related_company_field="candidate_id__recruitment_id__company_id"
    )
    history = HorillaAuditLog(
        related_name="history_set",
        bases=[
            HorillaAuditInfo,
        ],
    )

    def __str__(self) -> str:
        return super().__str__()


class StageFiles(HorillaModel):
    files = models.FileField(upload_to="recruitment/stageFiles", blank=True, null=True)

    def __str__(self):
        return self.files.name.split("/")[-1]


class StageNote(HorillaModel):
    """
    StageNote model
    """

    candidate_id = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    description = models.TextField(verbose_name=_("Description"), max_length=255)
    stage_id = models.ForeignKey(Stage, on_delete=models.CASCADE)
    stage_files = models.ManyToManyField(StageFiles, blank=True)
    updated_by = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True
    )
    candidate_can_view = models.BooleanField(default=False)
    objects = HorillaCompanyManager(
        related_company_field="candidate_id__recruitment_id__company_id"
    )

    def __str__(self) -> str:
        return f"{self.description}"

    def updated_user(self):
        if self.updated_by:
            return self.updated_by
        else:
            return self.candidate_id


class RecruitmentSurvey(HorillaModel):
    """
    RecruitmentSurvey model
    """

    question_types = [
        ("checkbox", _("Yes/No")),
        ("options", _("Choices")),
        ("multiple", _("Multiple Choice")),
        ("text", _("Text")),
        ("number", _("Number")),
        ("percentage", _("Percentage")),
        ("date", _("Date")),
        ("textarea", _("Textarea")),
        ("file", _("File Upload")),
        ("rating", _("Rating")),
    ]
    question = models.TextField(null=False, max_length=255)
    template_id = models.ManyToManyField(
        SurveyTemplate, verbose_name="Template", blank=True
    )
    is_mandatory = models.BooleanField(default=False)
    recruitment_ids = models.ManyToManyField(
        Recruitment,
        verbose_name=_("Recruitment"),
    )
    question = models.TextField(null=False)
    job_position_ids = models.ManyToManyField(
        JobPosition, verbose_name=_("Job Positions"), editable=False
    )
    sequence = models.IntegerField(null=True, default=0)
    type = models.CharField(
        max_length=15,
        choices=question_types,
    )
    options = models.TextField(
        null=True, default="", help_text=_("Separate choices by ',  '"), max_length=255
    )
    objects = HorillaCompanyManager(related_company_field="recruitment_ids__company_id")

    def __str__(self) -> str:
        return str(self.question)

    def choices(self):
        """
        Used to split the choices
        """
        return self.options.split(", ")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.template_id is None:
            general_template = SurveyTemplate.objects.filter(
                is_general_template=True
            ).first()
            if general_template:
                self.template_id.add(general_template)
                super().save(*args, **kwargs)

    class Meta:
        ordering = [
            "sequence",
        ]


class QuestionOrdering(HorillaModel):
    """
    Survey Template model
    """

    question_id = models.ForeignKey(RecruitmentSurvey, on_delete=models.CASCADE)
    recruitment_id = models.ForeignKey(Recruitment, on_delete=models.CASCADE)
    sequence = models.IntegerField(default=0)
    objects = HorillaCompanyManager(related_company_field="recruitment_ids__company_id")


class RecruitmentSurveyAnswer(HorillaModel):
    """
    RecruitmentSurveyAnswer
    """

    candidate_id = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    recruitment_id = models.ForeignKey(
        Recruitment,
        on_delete=models.PROTECT,
        verbose_name=_("Recruitment"),
        null=True,
    )
    job_position_id = models.ForeignKey(
        JobPosition,
        on_delete=models.PROTECT,
        verbose_name=_("Job Position"),
        null=True,
    )
    answer_json = models.JSONField()
    attachment = models.FileField(
        upload_to="recruitment_attachment", null=True, blank=True
    )
    objects = HorillaCompanyManager(related_company_field="recruitment_id__company_id")

    @property
    def answer(self):
        """
        Used to convert the json to dict
        """
        # Convert the JSON data to a dictionary
        try:
            return json.loads(self.answer_json)
        except json.JSONDecodeError:
            return {}  # Return an empty dictionary if JSON is invalid or empty

    def __str__(self) -> str:
        return f"{self.candidate_id.name}-{self.recruitment_id}"


class SkillZone(HorillaModel):
    """ "
    Model for talent pool
    """

    title = models.CharField(max_length=50, verbose_name="Skill Zone")
    description = models.TextField(verbose_name=_("Description"), max_length=255)
    company_id = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_("Company"),
    )
    objects = HorillaCompanyManager()

    class Meta:
        verbose_name = _("Skill Zone")
        verbose_name_plural = _("Skill Zones")

    def get_active(self):
        return SkillZoneCandidate.objects.filter(is_active=True, skill_zone_id=self)

    def __str__(self) -> str:
        return self.title


class SkillZoneCandidate(HorillaModel):
    """
    Model for saving candidate data's for future recruitment
    """

    skill_zone_id = models.ForeignKey(
        SkillZone,
        verbose_name=_("Skill Zone"),
        related_name="skillzonecandidate_set",
        on_delete=models.PROTECT,
        null=True,
    )
    candidate_id = models.ForeignKey(
        Candidate,
        on_delete=models.PROTECT,
        null=True,
        related_name="skillzonecandidate_set",
        verbose_name=_("Candidate"),
    )
    # job_position_id=models.ForeignKey(
    #     JobPosition,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     related_name="talent_pool",
    #     verbose_name=_("Job Position")
    # )

    reason = models.CharField(max_length=200, verbose_name=_("Reason"))
    added_on = models.DateField(auto_now_add=True)
    objects = HorillaCompanyManager(
        related_company_field="candidate_id__recruitment_id__company_id"
    )

    def clean(self):
        # Check for duplicate entries in the database
        duplicate_exists = (
            SkillZoneCandidate.objects.filter(
                candidate_id=self.candidate_id, skill_zone_id=self.skill_zone_id
            )
            .exclude(pk=self.pk)
            .exists()
        )

        if duplicate_exists:
            raise ValidationError(
                _(
                    f"Candidate {self.candidate_id} already exists in Skill Zone {self.skill_zone_id}."
                )
            )

        super().clean()

    def __str__(self) -> str:
        return str(self.candidate_id.get_full_name())


class CandidateRating(HorillaModel):
    employee_id = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="candidate_rating"
    )
    candidate_id = models.ForeignKey(
        Candidate, on_delete=models.PROTECT, related_name="candidate_rating"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    class Meta:
        unique_together = ["employee_id", "candidate_id"]

    def __str__(self) -> str:
        return f"{self.employee_id} - {self.candidate_id} rating {self.rating}"


class RecruitmentGeneralSetting(HorillaModel):
    """
    RecruitmentGeneralSettings model
    """

    candidate_self_tracking = models.BooleanField(default=False)
    show_overall_rating = models.BooleanField(default=False)
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)


class InterviewSchedule(HorillaModel):
    """
    Interview Scheduling Model
    """

    candidate_id = models.ForeignKey(
        Candidate,
        verbose_name=_("Candidate"),
        related_name="candidate_interview",
        on_delete=models.CASCADE,
    )
    employee_id = models.ManyToManyField(Employee, verbose_name=_("Interviewer"))
    interview_date = models.DateField(verbose_name=_("Interview Date"))
    interview_time = models.TimeField(verbose_name=_("Interview Time"))
    description = models.TextField(
        verbose_name=_("Description"), blank=True, max_length=255
    )
    completed = models.BooleanField(
        default=False, verbose_name=_("Is Interview Completed")
    )
    objects = HorillaCompanyManager("candidate_id__recruitment_id__company_id")

    def __str__(self) -> str:
        return f"{self.candidate_id} -Interview."

    class Meta:
        verbose_name = _("Schedule Interview")
        verbose_name_plural = _("Schedule Interviews")


class Resume(models.Model):
    file = models.FileField(
        upload_to="recruitment/resume",
        validators=[
            validate_pdf,
        ],
    )
    recruitment_id = models.ForeignKey(
        Recruitment, on_delete=models.CASCADE, related_name="resume"
    )
    is_candidate = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.recruitment_id} - Resume {self.pk}"


STATUS = [
    ("requested", "Requested"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]

FORMATS = [
    ("any", "Any"),
    ("pdf", "PDF"),
    ("txt", "TXT"),
    ("docx", "DOCX"),
    ("xlsx", "XLSX"),
    ("jpg", "JPG"),
    ("png", "PNG"),
    ("jpeg", "JPEG"),
]


class CandidateDocumentRequest(HorillaModel):
    title = models.CharField(max_length=100)
    candidate_id = models.ManyToManyField(Candidate)
    format = models.CharField(choices=FORMATS, max_length=10)
    max_size = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True, max_length=255)
    objects = HorillaCompanyManager(
        related_company_field="employee_id__employee_work_info__company_id"
    )

    def __str__(self):
        return self.title


class CandidateDocument(HorillaModel):
    title = models.CharField(max_length=250)
    candidate_id = models.ForeignKey(
        Candidate, on_delete=models.PROTECT, verbose_name="Candidate"
    )
    document_request_id = models.ForeignKey(
        CandidateDocumentRequest, on_delete=models.PROTECT, null=True
    )
    document = models.FileField(upload_to="candidate/documents", null=True)
    status = models.CharField(choices=STATUS, max_length=10, default="requested")
    reject_reason = models.TextField(blank=True, null=True, max_length=255)

    def __str__(self):
        return f"{self.candidate_id} - {self.title}"

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        file = self.document

        if len(self.title) < 3:
            raise ValidationError({"title": _("Title must be at least 3 characters")})

        if file and self.document_request_id:
            format = self.document_request_id.format
            max_size = self.document_request_id.max_size
            if max_size:
                if file.size > max_size * 1024 * 1024:
                    raise ValidationError(
                        {"document": _("File size exceeds the limit")}
                    )

            ext = file.name.split(".")[1].lower()
            if format == "any":
                pass
            elif ext != format:
                raise ValidationError(
                    {"document": _("Please upload {} file only.").format(format)}
                )


class LinkedInAccount(HorillaModel):
    username = models.CharField(max_length=250, verbose_name="Username")
    email = models.EmailField(max_length=254, verbose_name=_("Email"))
    api_token = models.CharField(max_length=500, verbose_name="API Token")
    sub_id = models.CharField(max_length=250, unique=True)
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.username)

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {self.api_token}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if not data["email"] == self.email:
                raise ValidationError({"email": _("Email mismatched.")})
            self.sub_id = response.json()["sub"]
        else:
            raise ValidationError(_("Check the credentials"))

    def action_template(self):
        """
        This method for get custom column for managers.
        """
        return render_template(
            path="linkedin/linkedin_action.html",
            context={"instance": self},
        )

    def is_active_toggle(self):
        """
        For toggle is_active field
        """
        url = f"update-isactive-linkedin-account/{self.id}"
        return render_template(
            path="is_active_toggle.html",
            context={"instance": self, "url": url},
        )


class CandidateApplication(HorillaModel):
    """
    CandidateApplication junction model for multiple recruitments per candidate
    This model represents a specific application instance to a recruitment
    """

    choices = [("male", _("Male")), ("female", _("Female")), ("other", _("Other"))]
    offer_letter_statuses = [
        ("not_sent", _("Not Sent")),
        ("sent", _("Sent")),
        ("accepted", _("Accepted")),
        ("rejected", _("Rejected")),
        ("joined", _("Joined")),
    ]
    source_choices = [
        ("application", _("Application Form")),
        ("software", _("Inside software")),
        ("other", _("Other")),
    ]

    # Core identity fields
    name = models.CharField(max_length=100, null=True, verbose_name=_("Name"))
    email = models.EmailField(max_length=254, verbose_name=_("Email"))
    profile = models.ImageField(upload_to=candidate_photo_upload_path, null=True)
    portfolio = models.URLField(max_length=200, blank=True)
    mobile = models.CharField(
        max_length=15,
        blank=True,
        validators=[validate_mobile],
        verbose_name=_("Mobile"),
    )
    resume = models.FileField(
        upload_to="recruitment/resume",
        validators=[validate_pdf],
    )
    
    # Personal information
    address = models.TextField(
        null=True, blank=True, verbose_name=_("Address"), max_length=255
    )
    country = models.CharField(
        max_length=30, null=True, blank=True, verbose_name=_("Country")
    )
    dob = models.DateField(null=True, blank=True, verbose_name=_("Date of Birth"))
    state = models.CharField(
        max_length=30, null=True, blank=True, verbose_name=_("State")
    )
    city = models.CharField(
        max_length=30, null=True, blank=True, verbose_name=_("City")
    )
    zip = models.CharField(
        max_length=30, null=True, blank=True, verbose_name=_("Zip Code")
    )
    gender = models.CharField(
        max_length=15,
        choices=choices,
        null=True,
        default="male",
        verbose_name=_("Gender"),
    )

    # Application-specific relationships
    recruitment_id = models.ForeignKey(
        Recruitment,
        on_delete=models.PROTECT,
        null=True,
        related_name="candidate_applications",
        verbose_name=_("Recruitment"),
    )
    job_position_id = models.ForeignKey(
        JobPosition,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Job Position"),
    )
    stage_id = models.ForeignKey(
        Stage,
        on_delete=models.PROTECT,
        null=True,
        verbose_name=_("Stage"),
    )
    converted_employee_id = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="candidate_application_get",
        verbose_name=_("Employee"),
    )
    referral = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="candidate_application_referral",
        verbose_name=_("Referral"),
    )

    # Application status and timeline
    schedule_date = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Schedule date")
    )
    source = models.CharField(
        max_length=20,
        choices=source_choices,
        null=True,
        blank=True,
        verbose_name=_("Source"),
    )
    start_onboard = models.BooleanField(default=False, verbose_name=_("Start Onboard"))
    hired = models.BooleanField(default=False, verbose_name=_("Hired"))
    canceled = models.BooleanField(default=False, verbose_name=_("Canceled"))
    converted = models.BooleanField(default=False, verbose_name=_("Converted"))
    joining_date = models.DateField(
        blank=True, null=True, verbose_name=_("Joining Date")
    )
    sequence = models.IntegerField(null=True, default=0)
    probation_end = models.DateField(null=True, editable=False)
    offer_letter_status = models.CharField(
        max_length=10,
        choices=offer_letter_statuses,
        default="not_sent",
        editable=False,
        verbose_name=_("Offer Letter Status"),
    )
    last_updated = models.DateField(null=True, auto_now=True)
    hired_date = models.DateField(null=True, blank=True, editable=False)

    # Audit trail
    history = HorillaAuditLog(
        related_name="application_history_set",
        bases=[HorillaAuditInfo],
    )

    # Manager and notification settings
    objects = HorillaCompanyManager(related_company_field="recruitment_id__company_id")
    converted_employee_id.exclude_from_automation = True
    mail_to_related_fields = [
        ("stage_id__stage_managers__get_mail", "Stage Managers"),
        ("recruitment_id__recruitment_managers__get_mail", "Recruitment Managers"),
    ]

    def __str__(self):
        return f"{self.name} - {self.recruitment_id.title if self.recruitment_id else 'No Recruitment'}"

    def is_offer_rejected(self):
        """
        Is offer rejected checking method
        """
        first = RejectedCandidate.objects.filter(candidate_id=self).first()
        if first:
            return first.reject_reason_id.count() > 0
        return first

    def get_full_name(self):
        """
        Method will return candidate full name
        """
        return str(self.name)

    def get_avatar(self):
        """
        Method will return the api to the avatar or path to the profile image
        """
        url = (
            f"https://ui-avatars.com/api/?name={self.get_full_name()}&background=random"
        )
        if self.profile:
            full_filename = self.profile.name
            if default_storage.exists(full_filename):
                url = self.profile.url
        return url

    def get_company(self):
        """
        This method is used to return the company
        """
        return getattr(
            getattr(getattr(self, "recruitment_id", None), "company_id", None),
            "company",
            None,
        )

    def get_job_position(self):
        """
        This method is used to return the job position of the candidate
        """
        return self.job_position_id.job_position if self.job_position_id else None

    def get_email(self):
        """
        Return email
        """
        return self.email

    def get_mail(self):
        """
        Return email for mail functionality
        """
        return self.get_email()

    def phone(self):
        return self.mobile

    def tracking(self):
        """
        This method is used to return the tracked history of the instance
        """
        return get_diff(self)

    def get_last_sent_mail(self):
        """
        This method is used to get last send mail
        """
        from base.models import EmailLog

        return (
            EmailLog.objects.filter(to__icontains=self.email)
            .order_by("-created_at")
            .first()
        )

    def get_interview(self):
        """
        This method is used to get the interview dates and times for the candidate for the mail templates
        """
        interviews = InterviewScheduleApplication.objects.filter(candidate_application_id=self.id)
        if interviews:
            interview_info = "<table>"
            interview_info += "<tr><th>Sl No.</th><th>Date</th><th>Time</th><th>Is Completed</th></tr>"
            for index, interview in enumerate(interviews, start=1):
                interview_info += f"<tr><td>{index}</td>"
                interview_info += (
                    f"<td class='dateformat_changer'>{interview.interview_date}</td>"
                )
                interview_info += (
                    f"<td class='timeformat_changer'>{interview.interview_time}</td>"
                )
                interview_info += (
                    f"<td>{'Yes' if interview.completed else 'No'}</td></tr>"
                )
            interview_info += "</table>"
            return interview_info
        else:
            return ""

    def save(self, *args, **kwargs):
        if self.stage_id is not None:
            self.hired = self.stage_id.stage_type == "selected"

        if not self.recruitment_id.is_event_based and self.job_position_id is None:
            self.job_position_id = self.recruitment_id.job_position_id
        if self.job_position_id not in self.recruitment_id.open_positions.all():
            raise ValidationError({"job_position_id": _("Choose valid choice")})
        if self.recruitment_id.is_event_based and self.job_position_id is None:
            raise ValidationError({"job_position_id": _("This field is required.")})
        if self.stage_id and self.stage_id.stage_type == "cancelled":
            self.canceled = True
        if self.canceled:
            cancelled_stage = Stage.objects.filter(
                recruitment_id=self.recruitment_id, stage_type="cancelled"
            ).first()
            if not cancelled_stage:
                cancelled_stage = Stage.objects.create(
                    recruitment_id=self.recruitment_id,
                    stage="Cancelled Candidates",
                    stage_type="cancelled",
                    sequence=50,
                )
            self.stage_id = cancelled_stage
        if (
            self.converted_employee_id
            and CandidateApplication.objects.filter(
                converted_employee_id=self.converted_employee_id
            )
            .exclude(id=self.id)
            .exists()
        ):
            raise ValidationError(_("Employee is unique for candidate application"))

        if self.converted:
            self.hired = False
            self.canceled = False

        super().save(*args, **kwargs)

    class Meta:
        """
        Meta class to add the additional info
        """
        unique_together = (
            "email",
            "recruitment_id",
        )
        permissions = (
            ("view_application_history", "View Application History"),
            ("archive_candidate_application", "Archive Candidate Application"),
        )
        ordering = ["sequence"]
        verbose_name = _("Candidate Application")
        verbose_name_plural = _("Candidate Applications")


class InterviewScheduleApplication(HorillaModel):
    """
    Interview Scheduling Model for CandidateApplication
    """

    candidate_application_id = models.ForeignKey(
        CandidateApplication,
        verbose_name=_("Candidate Application"),
        related_name="candidate_application_interview",
        on_delete=models.CASCADE,
    )
    employee_id = models.ManyToManyField(Employee, verbose_name=_("Interviewer"))
    interview_date = models.DateField(verbose_name=_("Interview Date"))
    interview_time = models.TimeField(verbose_name=_("Interview Time"))
    description = models.TextField(
        verbose_name=_("Description"), blank=True, max_length=255
    )
    completed = models.BooleanField(
        default=False, verbose_name=_("Is Interview Completed")
    )
    objects = HorillaCompanyManager("candidate_application_id__recruitment_id__company_id")

    def __str__(self) -> str:
        return f"{self.candidate_application_id} - Interview."

    class Meta:
        verbose_name = _("Schedule Interview Application")
        verbose_name_plural = _("Schedule Interview Applications")


class StageNoteApplication(HorillaModel):
    """
    StageNote model for CandidateApplication
    """

    candidate_application_id = models.ForeignKey(CandidateApplication, on_delete=models.CASCADE)
    description = models.TextField(verbose_name=_("Description"), max_length=255)
    stage_id = models.ForeignKey(Stage, on_delete=models.CASCADE)
    stage_files = models.ManyToManyField(StageFiles, blank=True)
    updated_by = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True
    )
    candidate_can_view = models.BooleanField(default=False)
    objects = HorillaCompanyManager(
        related_company_field="candidate_application_id__recruitment_id__company_id"
    )

    def __str__(self) -> str:
        return f"{self.description}"

    def updated_user(self):
        if self.updated_by:
            return self.updated_by
        else:
            return self.candidate_application_id

    class Meta:
        verbose_name = _("Stage Note Application")
        verbose_name_plural = _("Stage Notes Application")


class RecruitmentSurveyAnswerApplication(HorillaModel):
    """
    RecruitmentSurveyAnswer for CandidateApplication
    """

    candidate_application_id = models.ForeignKey(CandidateApplication, on_delete=models.CASCADE)
    recruitment_id = models.ForeignKey(
        Recruitment,
        on_delete=models.PROTECT,
        verbose_name=_("Recruitment"),
        null=True,
    )
    job_position_id = models.ForeignKey(
        JobPosition,
        on_delete=models.PROTECT,
        verbose_name=_("Job Position"),
        null=True,
    )
    answer_json = models.JSONField()
    attachment = models.FileField(
        upload_to="recruitment_attachment", null=True, blank=True
    )
    objects = HorillaCompanyManager(related_company_field="recruitment_id__company_id")

    @property
    def answer(self):
        """
        Used to convert the json to dict
        """
        try:
            return json.loads(self.answer_json)
        except json.JSONDecodeError:
            return {}

    def __str__(self) -> str:
        return f"{self.candidate_application_id.name}-{self.recruitment_id}"

    class Meta:
        verbose_name = _("Survey Answer Application")
        verbose_name_plural = _("Survey Answers Application")


class CandidateWorkExperience(HorillaModel):
    """
    Model for candidate work experience entries
    """
    
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='work_experiences',
        verbose_name=_("Candidate")
    )
    
    # Company Information
    company_name = models.CharField(
        max_length=200,
        verbose_name=_("Company Name")
    )
    company_website = models.URLField(
        max_length=200,
        blank=True,
        verbose_name=_("Company Website")
    )
    company_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Company Location")
    )
    
    # Position Information
    job_title = models.CharField(
        max_length=200,
        verbose_name=_("Job Title")
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Department")
    )
    
    # Duration
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date")
    )
    is_current = models.BooleanField(
        default=False,
        verbose_name=_("Currently Working Here")
    )
    
    # Description
    job_description = models.TextField(
        blank=True,
        verbose_name=_("Job Description")
    )
    achievements = models.TextField(
        blank=True,
        verbose_name=_("Key Achievements")
    )
    
    # Employment Type
    employment_type_choices = [
        ("full_time", _("Full Time")),
        ("part_time", _("Part Time")),
        ("contract", _("Contract")),
        ("internship", _("Internship")),
        ("freelance", _("Freelance")),
    ]
    employment_type = models.CharField(
        max_length=20,
        choices=employment_type_choices,
        default="full_time",
        verbose_name=_("Employment Type")
    )
    
    # Salary Information (Optional)
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Salary")
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        verbose_name=_("Currency")
    )
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = _("Work Experience")
        verbose_name_plural = _("Work Experiences")


class CandidateWorkProject(HorillaModel):
    """
    Model for candidate work projects within work experience
    """
    
    work_experience = models.ForeignKey(
        CandidateWorkExperience,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name=_("Work Experience")
    )
    
    project_name = models.CharField(
        max_length=200,
        verbose_name=_("Project Name")
    )
    project_description = models.TextField(
        verbose_name=_("Project Description")
    )
    technologies_used = models.TextField(
        blank=True,
        verbose_name=_("Technologies Used")
    )
    project_url = models.URLField(
        max_length=200,
        blank=True,
        verbose_name=_("Project URL")
    )
    
    # Project Duration
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Project Start Date")
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Project End Date")
    )
    is_current = models.BooleanField(
        default=False,
        verbose_name=_("Currently Working on This Project")
    )
    
    # Project Role
    role = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Role in Project")
    )
    
    def __str__(self):
        return f"{self.project_name} - {self.work_experience.job_title}"
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = _("Work Project")
        verbose_name_plural = _("Work Projects")


class CandidateEducation(HorillaModel):
    """
    Model for candidate education entries
    """
    
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='education',
        verbose_name=_("Candidate")
    )
    
    # Institution Information
    institution_name = models.CharField(
        max_length=200,
        verbose_name=_("Institution Name")
    )
    institution_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Institution Location")
    )
    institution_website = models.URLField(
        max_length=200,
        blank=True,
        verbose_name=_("Institution Website")
    )
    
    # Degree Information
    degree_name = models.CharField(
        max_length=200,
        verbose_name=_("Degree Name")
    )
    field_of_study = models.CharField(
        max_length=200,
        verbose_name=_("Field of Study")
    )
    
    # Dates
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Start Date")
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date")
    )
    graduation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Graduation Date")
    )
    is_current = models.BooleanField(
        default=False,
        verbose_name=_("Currently Studying")
    )
    
    # Academic Information
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("GPA")
    )
    max_gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=4.00,
        verbose_name=_("Maximum GPA")
    )
    
    # Additional Information
    honors = models.TextField(
        blank=True,
        verbose_name=_("Honors & Awards")
    )
    activities = models.TextField(
        blank=True,
        verbose_name=_("Activities & Societies")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    
    def __str__(self):
        return f"{self.degree_name} in {self.field_of_study} from {self.institution_name}"
    
    class Meta:
        ordering = ['-graduation_date', '-end_date']
        verbose_name = _("Education")
        verbose_name_plural = _("Education")


class CandidateCertification(HorillaModel):
    """
    Model for candidate certifications
    """
    
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='certifications',
        verbose_name=_("Candidate")
    )
    
    # Certification Information
    certification_name = models.CharField(
        max_length=200,
        verbose_name=_("Certification Name")
    )
    issuing_organization = models.CharField(
        max_length=200,
        verbose_name=_("Issuing Organization")
    )
    organization_website = models.URLField(
        max_length=200,
        blank=True,
        verbose_name=_("Organization Website")
    )
    
    # Dates
    issue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Issue Date")
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expiry Date")
    )
    is_current = models.BooleanField(
        default=True,
        verbose_name=_("Currently Valid")
    )
    
    # Credential Information
    credential_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Credential ID")
    )
    credential_url = models.URLField(
        max_length=200,
        blank=True,
        verbose_name=_("Credential URL")
    )
    
    # Additional Information
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    skills_covered = models.TextField(
        blank=True,
        verbose_name=_("Skills Covered")
    )
    
    def __str__(self):
        return f"{self.certification_name} from {self.issuing_organization}"
    
    class Meta:
        ordering = ['-issue_date']
        verbose_name = _("Certification")
        verbose_name_plural = _("Certifications")


class CandidateSkill(HorillaModel):
    """
    Model for candidate skills
    """
    
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name=_("Candidate")
    )
    
    # Skill Information
    skill_name = models.CharField(
        max_length=100,
        verbose_name=_("Skill Name")
    )
    
    # Skill Categories
    skill_category_choices = [
        ("technical", _("Technical Skills")),
        ("soft", _("Soft Skills")),
        ("language", _("Languages")),
        ("tool", _("Tools & Technologies")),
        ("framework", _("Frameworks & Libraries")),
        ("methodology", _("Methodologies")),
        ("other", _("Other")),
    ]
    skill_category = models.CharField(
        max_length=20,
        choices=skill_category_choices,
        default="technical",
        verbose_name=_("Skill Category")
    )
    
    # Proficiency Level
    proficiency_choices = [
        ("beginner", _("Beginner")),
        ("intermediate", _("Intermediate")),
        ("advanced", _("Advanced")),
        ("expert", _("Expert")),
    ]
    proficiency_level = models.CharField(
        max_length=20,
        choices=proficiency_choices,
        default="intermediate",
        verbose_name=_("Proficiency Level")
    )
    
    # Years of Experience
    years_of_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Years of Experience")
    )
    
    # Additional Information
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    is_highlighted = models.BooleanField(
        default=False,
        verbose_name=_("Highlighted Skill")
    )
    
    def __str__(self):
        return f"{self.skill_name} ({self.get_proficiency_level_display()})"
    
    class Meta:
        ordering = ['skill_category', 'skill_name']
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        unique_together = ['candidate', 'skill_name']


class CandidateSkillRating(HorillaModel):
    """
    Model for candidate skill ratings
    """
    
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='skill_ratings',
        verbose_name=_("Candidate")
    )
    
    # Recruitment context
    recruitment = models.ForeignKey(
        Recruitment,
        on_delete=models.CASCADE,
        related_name='skill_ratings',
        verbose_name=_("Recruitment"),
        null=True,
        blank=True
    )
    
    # Stage context
    stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        related_name='skill_ratings',
        verbose_name=_("Stage"),
        null=True,
        blank=True
    )
    
    # Skill Information
    skill_name = models.CharField(
        max_length=100,
        verbose_name=_("Skill Name")
    )
    
    # Skill Categories
    skill_category_choices = [
        ("technical", _("Technical Skills")),
        ("non_technical", _("Non-Technical Skills")),
    ]
    skill_category = models.CharField(
        max_length=20,
        choices=skill_category_choices,
        default="technical",
        verbose_name=_("Skill Category")
    )
    
    # Rating (0.0 to 5.0)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(5.0)
        ],
        verbose_name=_("Rating (0.0 - 5.0)")
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    # Rated by
    rated_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='skill_ratings_given',
        verbose_name=_("Rated By")
    )
    
    # Rating date
    rated_on = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Rated On")
    )
    
    def __str__(self):
        context = []
        if self.recruitment:
            context.append(f"Rec: {self.recruitment.title}")
        if self.stage:
            context.append(f"Stage: {self.stage.stage}")
        context_str = " | ".join(context) if context else "General"
        return f"{self.candidate.name} - {self.skill_name}: {self.rating}/5.0 ({context_str})"
    
    class Meta:
        ordering = ['-rated_on']
        verbose_name = _("Skill Rating")
        verbose_name_plural = _("Skill Ratings")
        unique_together = ['candidate', 'skill_name', 'rated_by', 'recruitment', 'stage']
