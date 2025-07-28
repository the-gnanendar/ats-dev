"""
forms.py

This module contains the form classes used in the application.

Each form represents a specific functionality or data input in the
application. They are responsible for validating
and processing user input data.

Classes:
- YourForm: Represents a form for handling specific data input.

Usage:
from django import forms

class YourForm(forms.Form):
    field_name = forms.CharField()

    def clean_field_name(self):
        # Custom validation logic goes here
        pass
"""

import logging
import uuid
from ast import Dict
from datetime import date, datetime
from typing import Any

from django import forms
from django.forms import inlineformset_factory
from django.apps import apps
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from base.forms import Form
from base.forms import ModelForm as BaseModelForm
from base.methods import reload_queryset
from employee.filters import EmployeeFilter
from employee.models import Employee
from horilla import horilla_middlewares
from horilla.horilla_middlewares import _thread_locals
from horilla_widgets.widgets.horilla_multi_select_field import HorillaMultiSelectField
from horilla_widgets.widgets.select_widgets import HorillaMultiSelectWidget
from recruitment import widgets
from recruitment.models import (
    Candidate,
    CandidateDocument,
    CandidateDocumentRequest,
    InterviewSchedule,
    JobPosition,
    Recruitment,
    RecruitmentSurvey,
    RejectedCandidate,
    RejectReason,
    Resume,
    Skill,
    TechnicalSkill,
    NonTechnicalSkill,
    SkillZone,
    SkillZoneCandidate,
    Stage,
    StageFiles,
    StageNote,
    SurveyTemplate,
    CandidateApplication,
    InterviewScheduleApplication,
    StageNoteApplication,
    CandidateWorkExperience, CandidateWorkProject, 
    CandidateEducation, CandidateCertification, CandidateSkill, CandidateSkillRating, LinkedInAccount, Company
)

logger = logging.getLogger(__name__)


class ModelForm(forms.ModelForm):
    """
    Overriding django default model form to apply some styles
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = getattr(horilla_middlewares._thread_locals, "request", None)
        reload_queryset(self.fields)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.DateInput)):
                field.initial = date.today()

            if isinstance(
                widget,
                (forms.NumberInput, forms.EmailInput, forms.TextInput, forms.FileInput),
            ):
                label = _(field.label)
                field.widget.attrs.update(
                    {"class": "oh-input w-100", "placeholder": label}
                )
            elif isinstance(widget, forms.URLInput):
                field.widget.attrs.update(
                    {"class": "oh-input w-100", "placeholder": field.label}
                )
            elif isinstance(widget, (forms.Select,)):
                field.empty_label = _("---Choose {label}---").format(
                    label=_(field.label)
                )
                self.fields[field_name].widget.attrs.update(
                    {
                        "id": uuid.uuid4,
                        "class": "oh-select oh-select-2 w-100",
                        "style": "height:50px;",
                    }
                )
            elif isinstance(widget, (forms.Textarea)):
                label = _(field.label)
                field.widget.attrs.update(
                    {
                        "class": "oh-input w-100",
                        "placeholder": label,
                        "rows": 2,
                        "cols": 40,
                    }
                )
            elif isinstance(
                widget,
                (
                    forms.CheckboxInput,
                    forms.CheckboxSelectMultiple,
                ),
            ):
                field.widget.attrs.update({"class": "oh-switch__checkbox "})

            try:
                self.fields["employee_id"].initial = request.user.employee_get
            except:
                pass

            try:
                self.fields["company_id"].initial = (
                    request.user.employee_get.get_company
                )
            except:
                pass


class RegistrationForm(forms.ModelForm):
    """
    Overriding django default model form to apply some styles
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        reload_queryset(self.fields)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.Select,)):
                label = ""
                if field.label is not None:
                    label = _(field.label)
                field.empty_label = _("---Choose {label}---").format(label=label)
                self.fields[field_name].widget.attrs.update(
                    {"id": uuid.uuid4, "class": "oh-select-2 oh-select--sm w-100"}
                )
            elif isinstance(widget, (forms.TextInput)):
                field.widget.attrs.update(
                    {
                        "class": "oh-input w-100",
                    }
                )
            elif isinstance(
                widget,
                (
                    forms.CheckboxInput,
                    forms.CheckboxSelectMultiple,
                ),
            ):
                field.widget.attrs.update({"class": "oh-switch__checkbox "})


class DropDownForm(forms.ModelForm):
    """
    Overriding django default model form to apply some styles
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        reload_queryset(self.fields)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(
                widget,
                (
                    forms.NumberInput,
                    forms.EmailInput,
                    forms.TextInput,
                    forms.FileInput,
                    forms.URLInput,
                ),
            ):
                if field.label is not None:
                    label = _(field.label)
                    field.widget.attrs.update(
                        {
                            "class": "oh-input oh-input--small oh-table__add-new-row d-block w-100",
                            "placeholder": label,
                        }
                    )
            elif isinstance(widget, (forms.Select,)):
                self.fields[field_name].widget.attrs.update(
                    {
                        "class": "oh-select-2 oh-select--xs-forced ",
                        "id": uuid.uuid4(),
                    }
                )
            elif isinstance(widget, (forms.Textarea)):
                if field.label is not None:
                    label = _(field.label)
                    field.widget.attrs.update(
                        {
                            "class": "oh-input oh-input--small oh-input--textarea",
                            "placeholder": label,
                            "rows": 1,
                            "cols": 40,
                        }
                    )
            elif isinstance(
                widget,
                (
                    forms.CheckboxInput,
                    forms.CheckboxSelectMultiple,
                ),
            ):
                field.widget.attrs.update({"class": "oh-switch__checkbox "})


class RecruitmentCreationForm(BaseModelForm):
    """
    Form for Recruitment model
    """

    # survey_templates = forms.ModelMultipleChoiceField(
    #     queryset=SurveyTemplate.objects.all(),
    #     widget=forms.SelectMultiple(),
    #     label=_("Survey Templates"),
    #     required=False,
    # )
    # linkedin_account_id = forms.ModelChoiceField(
    #     queryset=LinkedInAccount.objects.filter(is_active=True)
    #     label=_('')
    # )
    class Meta:
        """
        Meta class to add the additional info
        """

        model = Recruitment
        fields = "__all__"
        exclude = ["is_active", "linkedin_post_id", "linkedin_account_id", "publish_in_linkedin"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "application_deadline": forms.DateInput(attrs={"type": "date"}),
            "job_summary": forms.Textarea(attrs={"data-summernote": "", "rows": 4}),
            "key_responsibilities": forms.Textarea(attrs={"data-summernote": "", "rows": 6}),
            "preferred_qualifications": forms.Textarea(attrs={"data-summernote": "", "rows": 4}),
        }

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("horilla_form.html", context)
        return table_html

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        reload_queryset(self.fields)
        if not self.instance.pk:
            self.fields["recruitment_managers"] = HorillaMultiSelectField(
                queryset=Employee.objects.filter(is_active=True),
                widget=HorillaMultiSelectWidget(
                    filter_route_name="employee-widget-filter",
                    filter_class=EmployeeFilter,
                    filter_instance_contex_name="f",
                    filter_template_path="employee_filters.html",
                    required=True,
                ),
                label=f"{self._meta.model()._meta.get_field('recruitment_managers').verbose_name}",
            )
            
            # Default Stage Manager field
            self.fields["default_stage_manager"] = HorillaMultiSelectField(
                queryset=Employee.objects.filter(is_active=True),
                widget=HorillaMultiSelectWidget(
                    filter_route_name="employee-widget-filter",
                    filter_class=EmployeeFilter,
                    filter_instance_contex_name="f",
                    filter_template_path="employee_filters.html",
                    required=False,
                ),
                label=f"{self._meta.model()._meta.get_field('default_stage_manager').verbose_name}",
            )
            
            # L1 Interviewer field
            self.fields["l1_interviewer"] = HorillaMultiSelectField(
                queryset=Employee.objects.filter(is_active=True),
                widget=HorillaMultiSelectWidget(
                    filter_route_name="employee-widget-filter",
                    filter_class=EmployeeFilter,
                    filter_instance_contex_name="f",
                    filter_template_path="employee_filters.html",
                    required=False,
                ),
                label=f"{self._meta.model()._meta.get_field('l1_interviewer').verbose_name}",
            )
            
            # L2 Interviewer field
            self.fields["l2_interviewer"] = HorillaMultiSelectField(
                queryset=Employee.objects.filter(is_active=True),
                widget=HorillaMultiSelectWidget(
                    filter_route_name="employee-widget-filter",
                    filter_class=EmployeeFilter,
                    filter_instance_contex_name="f",
                    filter_template_path="employee_filters.html",
                    required=False,
                ),
                label=f"{self._meta.model()._meta.get_field('l2_interviewer').verbose_name}",
            )
            
            # L3 Interviewer field
            self.fields["l3_interviewer"] = HorillaMultiSelectField(
                queryset=Employee.objects.filter(is_active=True),
                widget=HorillaMultiSelectWidget(
                    filter_route_name="employee-widget-filter",
                    filter_class=EmployeeFilter,
                    filter_instance_contex_name="f",
                    filter_template_path="employee_filters.html",
                    required=False,
                ),
                label=f"{self._meta.model()._meta.get_field('l3_interviewer').verbose_name}",
            )

        technical_skill_choices = [("", _("---Choose Technical Skills---"))] + list(
            self.fields["technical_skills"].queryset.values_list("id", "title")
        )
        self.fields["technical_skills"].choices = technical_skill_choices
        self.fields["technical_skills"].choices += [("create", _("Create new technical skill "))]
        
        non_technical_skill_choices = [("", _("---Choose Non-Technical Skills---"))] + list(
            self.fields["non_technical_skills"].queryset.values_list("id", "title")
        )
        self.fields["non_technical_skills"].choices = non_technical_skill_choices
        self.fields["non_technical_skills"].choices += [("create", _("Create new non-technical skill "))]

    # def create_option(self, *args,**kwargs):
    #     option = super().create_option(*args,**kwargs)

    #     if option.get('value') == "create":
    #         option['attrs']['class'] = 'text-danger'

    #     return option

    def clean(self):
        if isinstance(self.fields["recruitment_managers"], HorillaMultiSelectField):
            ids = self.data.getlist("recruitment_managers")
            if ids:
                self.errors.pop("recruitment_managers", None)
        
        # Clean new fields
        for field_name in ["default_stage_manager", "l1_interviewer", "l2_interviewer", "l3_interviewer"]:
            if isinstance(self.fields.get(field_name), HorillaMultiSelectField):
                ids = self.data.getlist(field_name)
                if ids:
                    self.errors.pop(field_name, None)
        open_positions = self.cleaned_data.get("open_positions")
        is_published = self.cleaned_data.get("is_published")
        if is_published and not open_positions:
            raise forms.ValidationError(
                _("Job position is required if the recruitment is publishing.")
            )

        super().clean()


class StageCreationForm(BaseModelForm):
    """
    Form for Stage model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        model = Stage
        fields = "__all__"
        exclude = ["sequence", "is_active"]
        labels = {
            "stage": _("Stage"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        reload_queryset(self.fields)
        if not self.instance.pk:
            self.fields["stage_managers"] = HorillaMultiSelectField(
                queryset=Employee.objects.filter(is_active=True),
                widget=HorillaMultiSelectWidget(
                    filter_route_name="employee-widget-filter",
                    filter_class=EmployeeFilter,
                    filter_instance_contex_name="f",
                    filter_template_path="employee_filters.html",
                    required=True,
                ),
                label=f"{self._meta.model()._meta.get_field('stage_managers').verbose_name}",
            )
            self.fields["stage_interviewers"] = HorillaMultiSelectField(
                queryset=Employee.objects.filter(is_active=True),
                widget=HorillaMultiSelectWidget(
                    filter_route_name="employee-widget-filter",
                    filter_class=EmployeeFilter,
                    filter_instance_contex_name="f",
                    filter_template_path="employee_filters.html",
                    required=False,
                ),
                label=f"{self._meta.model()._meta.get_field('stage_interviewers').verbose_name}",
            )

    def clean(self):
        if isinstance(self.fields["stage_managers"], HorillaMultiSelectField):
            ids = self.data.getlist("stage_managers")
            if ids:
                self.errors.pop("stage_managers", None)
        if isinstance(self.fields["stage_interviewers"], HorillaMultiSelectField):
            ids = self.data.getlist("stage_interviewers")
            if ids:
                self.errors.pop("stage_interviewers", None)
        super().clean()


class CandidateCreationForm(BaseModelForm):
    """
    Form for Candidate model - recruitment-agnostic candidate profile
    Now includes comprehensive fields for work experience, education, skills, and certifications
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source"].initial = "software"
        self.fields["profile"].widget.attrs["accept"] = ".jpg, .jpeg, .png"
        self.fields["profile"].required = False
        self.fields["resume"].widget.attrs["accept"] = ".pdf"
        self.fields["resume"].required = True
        
        # Make only name, email, and resume mandatory
        self.fields["name"].required = True
        self.fields["email"].required = True
        self.fields["resume"].required = True
        
        # Make all other fields optional
        optional_fields = [
            "profile", "portfolio", "mobile", "dob", "gender", "address", 
            "source", "country", "state", "city", "zip", "referral", "is_active"
        ]
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

    class Meta:
        """
        Meta class to add the additional info
        """

        model = Candidate
        fields = [
            "profile",
            "name",
            "portfolio",
            "email",
            "mobile",
            "dob",
            "gender",
            "address",
            "source",
            "country",
            "state",
            "city",
            "zip",
            "resume",
            "referral",
            "is_active",
        ]

        widgets = {
            "profile": forms.FileInput(attrs={"accept": "image/*"}),
            "name": forms.TextInput(),
            "portfolio": forms.URLInput(),
            "email": forms.EmailInput(),
            "mobile": forms.TextInput(),
            "dob": forms.DateInput(attrs={"type": "date"}),
            "gender": forms.Select(),
            "address": forms.Textarea(attrs={"rows": 3}),
            "source": forms.Select(),
            "country": forms.Select(),
            "state": forms.Select(),
            "city": forms.TextInput(),
            "zip": forms.TextInput(),
            "resume": forms.FileInput(attrs={"accept": ".pdf,.doc,.docx"}),
            "referral": forms.Select(),
            "is_active": forms.CheckboxInput(),
        }

    def save(self, commit: bool = True):
        # Simple save for candidate profile
        return super().save(commit)

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string(
            "candidate/candidate_create_form_as_p.html", context
        )
        return table_html

    def clean(self):
        errors = {}
        name = self.cleaned_data.get("name")
        email = self.cleaned_data.get("email")
        resume = self.cleaned_data.get("resume")
        
        if not name:
            errors["name"] = _("Name is required")
        if not email:
            errors["email"] = _("Email is required")
        if not resume:
            errors["resume"] = _("Resume is required")
            
        if errors:
            raise ValidationError(errors)
        return super().clean()


class ApplicationForm(RegistrationForm):
    """
    Form for create Candidate
    """

    load = forms.CharField(widget=widgets.RecruitmentAjaxWidget, required=False)
    active_recruitment = Recruitment.objects.filter(
        is_active=True, closed=False, is_published=True
    )
    recruitment_id = forms.ModelChoiceField(queryset=active_recruitment)

    class Meta:
        """
        Meta class to add the additional info
        """

        model = Candidate
        exclude = (
            "stage_id",
            "schedule_date",
            "referral",
            "start_onboard",
            "hired",
            "is_active",
            "canceled",
            "joining_date",
            "sequence",
            "offerletter_status",
            "source",
        )
        widgets = {
            "recruitment_id": forms.TextInput(
                attrs={
                    "required": "required",
                }
            ),
            "dob": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = getattr(_thread_locals, "request", None)
        self.fields["profile"].widget.attrs["accept"] = ".jpg, .jpeg, .png"
        self.fields["profile"].required = False
        self.fields["resume"].widget.attrs["accept"] = ".pdf"
        self.fields["resume"].required = False

        self.fields["recruitment_id"].widget.attrs = {"data-widget": "ajax-widget"}
        if request and request.user.has_perm("recruitment.add_candidate"):
            self.fields["profile"].required = False

    def clean(self, *args, **kwargs):
        name = self.cleaned_data.get("name")
        request = getattr(_thread_locals, "request", None)

        errors = {}
        profile = self.cleaned_data.get("profile")
        resume = self.cleaned_data.get("resume")
        recruitment: Recruitment = self.cleaned_data.get("recruitment_id")

        if recruitment:
            if not resume and not recruitment.optional_resume:
                errors["resume"] = _("This field is required")
            if not profile and not recruitment.optional_profile_image:
                errors["profile"] = _("This field is required")

        if errors:
            raise ValidationError(errors)

        if (
            not profile
            and request
            and request.user.has_perm("recruitment.add_candidate")
        ):
            profile_pic_url = f"https://ui-avatars.com/api/?name={name}"
            self.cleaned_data["profile"] = profile_pic_url

        super().clean()
        return self.cleaned_data


class RecruitmentDropDownForm(DropDownForm):
    """
    Form for Recruitment model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        fields = "__all__"
        exclude = ["is_active", "linkedin_post_id", "linkedin_account_id", "publish_in_linkedin"]
        model = Recruitment
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "application_deadline": forms.DateInput(attrs={"type": "date"}),
            "job_summary": forms.Textarea(attrs={"data-summernote": "", "rows": 4}),
            "key_responsibilities": forms.Textarea(attrs={"data-summernote": "", "rows": 6}),
            "preferred_qualifications": forms.Textarea(attrs={"data-summernote": "", "rows": 4}),
        }
        labels = {"vacancy": _("Vacancy")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recruitment_managers"].widget.attrs.update({"id": uuid.uuid4})


class AddCandidateForm(ModelForm):
    """
    Form for Candidate model - simple candidate profile creation
    Note: This form is deprecated. Use CandidateApplication for recruitment-specific operations.
    """

    verbose_name = "Add Candidate"

    class Meta:
        """
        Meta class to add the additional info
        """

        model = Candidate
        fields = [
            "profile",
            "resume",
            "name",
            "email",
            "mobile",
            "gender",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profile"].widget.attrs["accept"] = ".jpg, .jpeg, .png"
        self.fields["resume"].widget.attrs["accept"] = ".pdf"
        self.fields["profile"].required = False
        self.fields["resume"].required = False
        self.fields["gender"].empty_label = None

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class StageDropDownForm(DropDownForm):
    """
    Form for Stage model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        model = Stage
        fields = "__all__"
        exclude = ["sequence", "is_active"]
        labels = {
            "stage": _("Stage"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stage = Stage.objects.last()
        if stage is not None and stage.sequence is not None:
            self.instance.sequence = stage.sequence + 1
        else:
            self.instance.sequence = 1


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [
                single_file_clean(data, initial),
            ]
        return result[0] if result else []


class StageNoteForm(ModelForm):
    """
    Form for StageNote model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        model = StageNote
        # exclude = (
        #     "updated_by",
        #     "stage_id",
        # )
        fields = ["description"]
        exclude = ["is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # field = self.fields["candidate_id"]
        # field.widget = field.hidden_widget()
        self.fields["stage_files"] = MultipleFileField(label="files")
        self.fields["stage_files"].required = False

    def save(self, commit: bool = ...) -> Any:
        attachment = []
        multiple_attachment_ids = []
        attachments = None
        if self.files.getlist("stage_files"):
            attachments = self.files.getlist("stage_files")
            self.instance.attachement = attachments[0]
            multiple_attachment_ids = []

            for attachment in attachments:
                file_instance = StageFiles()
                file_instance.files = attachment
                file_instance.save()
                multiple_attachment_ids.append(file_instance.pk)
        instance = super().save(commit)
        if commit:
            instance.stage_files.add(*multiple_attachment_ids)
        return instance, multiple_attachment_ids


class StageNoteUpdateForm(ModelForm):
    class Meta:
        """
        Meta class to add the additional info
        """

        model = StageNote
        exclude = ["updated_by", "stage_id", "stage_files", "is_active"]
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["candidate_id"]
        field.widget = field.hidden_widget()


class QuestionForm(ModelForm):
    """
    QuestionForm
    """

    verbose_name = "Survey Questions"

    recruitment = forms.ModelMultipleChoiceField(
        queryset=Recruitment.objects.filter(is_active=True),
        required=False,
        label=_("Recruitment"),
    )
    options = forms.CharField(
        widget=forms.TextInput, label=_("Options"), required=False
    )

    class Meta:
        """
        Class Meta for additional options
        """

        model = RecruitmentSurvey
        fields = "__all__"
        exclude = ["recruitment_ids", "job_position_ids", "is_active", "options"]
        labels = {
            "question": _("Question"),
            "sequence": _("Sequence"),
            "type": _("Type"),
            "options": _("Options"),
            "is_mandatory": _("Is Mandatory"),
        }

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string(
            "survey/question_template_organized_form.html", context
        )
        return table_html

    def clean(self):
        cleaned_data = super().clean()
        recruitment = self.cleaned_data["recruitment"]
        question_type = self.cleaned_data["type"]
        options = self.cleaned_data.get("options")
        if not recruitment.exists():  # or jobs.exists()):
            raise ValidationError(
                {"recruitment": _("Choose any recruitment to apply this question")}
            )
        self.recruitment = recruitment
        if question_type in ["options", "multiple"] and (
            options is None or options == ""
        ):
            raise ValidationError({"options": "Options field is required"})
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.type in ["options", "multiple"]:
            additional_options = []
            for key, value in self.cleaned_data.items():
                if key.startswith("options") and value:
                    additional_options.append(value)

            instance.options = ", ".join(additional_options)
            if commit:
                instance.save()
                self.save_m2m()
        else:
            instance.options = ""
        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        self.option_count = 1

        def create_options_field(option_key, initial=None):
            self.fields[option_key] = forms.CharField(
                widget=forms.TextInput(
                    attrs={
                        "name": option_key,
                        "id": f"id_{option_key}",
                        "class": "oh-input w-100",
                    }
                ),
                label=_("Options"),
                required=False,
                initial=initial,
            )

        if instance:
            split_options = instance.options.split(",")
            for i, option in enumerate(split_options):
                if i == 0:
                    create_options_field("options", option)
                else:
                    self.option_count += 1
                    create_options_field(f"options{i}", option)

        if instance:
            self.fields["recruitment"].initial = instance.recruitment_ids.all()
        self.fields["type"].widget.attrs.update(
            {"class": " w-100", "style": "border:solid 1px #6c757d52;height:50px;"}
        )
        for key, value in self.data.items():
            if key.startswith("options"):
                self.option_count += 1
                create_options_field(key, initial=value)
        fields_order = list(self.fields.keys())
        fields_order.remove("recruitment")
        fields_order.insert(2, "recruitment")
        self.fields = {field: self.fields[field] for field in fields_order}


class SurveyForm(forms.Form):
    """
    SurveyTemplateForm
    """

    def __init__(self, recruitment, *args, **kwargs) -> None:
        super().__init__(recruitment, *args, **kwargs)
        questions = recruitment.recruitmentsurvey_set.all()
        all_questions = RecruitmentSurvey.objects.none() | questions
        for template in recruitment.survey_templates.all():
            questions = template.recruitmentsurvey_set.all()
            all_questions = all_questions | questions
        context = {"form": self, "questions": all_questions.distinct()}
        form = render_to_string("survey_form.html", context)
        self.form = form
        return
        # for question in questions:
        # self


class SurveyPreviewForm(forms.Form):
    """
    SurveyTemplateForm
    """

    def __init__(self, template, *args, **kwargs) -> None:
        super().__init__(template, *args, **kwargs)
        all_questions = RecruitmentSurvey.objects.filter(template_id__in=[template])
        context = {"form": self, "questions": all_questions.distinct()}
        form = render_to_string("survey_preview_form.html", context)
        self.form = form
        return
        # for question in questions:
        # self


class TemplateForm(BaseModelForm):
    """
    TemplateForm
    """

    class Meta:
        model = SurveyTemplate
        fields = "__all__"
        exclude = ["is_active"]

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class AddQuestionForm(Form):
    """
    AddQuestionForm
    """

    verbose_name = "Add Question"
    question_ids = forms.ModelMultipleChoiceField(
        queryset=RecruitmentSurvey.objects.all(), label="Questions"
    )
    template_ids = forms.ModelMultipleChoiceField(
        queryset=SurveyTemplate.objects.all(), label="Templates"
    )

    def save(self):
        """
        Manual save/adding of questions to the templates
        """
        for question in self.cleaned_data["question_ids"]:
            question.template_id.add(*self.data["template_ids"])

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


exclude_fields = [
    "id",
    "profile",
    "portfolio", 
    "resume",
    "created_at",
    "created_by",
    "modified_by",
    "is_active",
    "last_updated",
    "horilla_history",
]


class CandidateExportForm(forms.Form):
    model_fields = Candidate._meta.get_fields()
    field_choices = [
        (field.name, field.verbose_name.capitalize())
        for field in model_fields
        if hasattr(field, "verbose_name") and field.name not in exclude_fields
    ]
    selected_fields = forms.MultipleChoiceField(
        choices=field_choices,
        widget=forms.CheckboxSelectMultiple,
        initial=[
            "name",
            "email",
            "mobile",
            "gender",
            "source",
            "country",
            "state",
            "city",
        ],
    )


class SkillZoneCreateForm(BaseModelForm):

    class Meta:
        """
        Class Meta for additional options
        """

        model = SkillZone
        fields = "__all__"
        exclude = ["is_active"]


class SkillZoneCandidateForm(BaseModelForm):
    verbose_name = _("Skill Zone Candidate")
    candidate_id = forms.ModelMultipleChoiceField(
        queryset=Candidate.objects.all(),
        widget=forms.SelectMultiple,
        label=_("Candidate"),
    )

    class Meta:
        """
        Class Meta for additional options
        """

        model = SkillZoneCandidate
        fields = "__all__"
        exclude = [
            "added_on",
            "is_active",
        ]

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html

    def clean_candidate_id(self):
        selected_candidates = self.cleaned_data["candidate_id"]

        # Ensure all selected candidates are instances of the Candidate model
        for candidate in selected_candidates:
            if not isinstance(candidate, Candidate):
                raise forms.ValidationError("Invalid candidate selected.")

        return selected_candidates.first()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["candidate_id"].empty_label = None
        if self.instance.pk:
            self.verbose_name = (
                self.instance.candidate_id.name
                + " / "
                + self.instance.skill_zone_id.title
            )

    def save(self, commit: bool = True) -> SkillZoneCandidate:

        if not self.instance.pk:
            candidates = Candidate.objects.filter(
                id__in=list((self.data.getlist("candidate_id")))
            )
            skill_zone = self.cleaned_data["skill_zone_id"]
            reason = self.cleaned_data["reason"]
            for candidate in candidates:
                zone_cand = SkillZoneCandidate()
                zone_cand.skill_zone_id = skill_zone
                zone_cand.candidate_id = candidate
                zone_cand.reason = reason
                zone_cand.save()
        else:
            instance = super().save()

        return self.instance


class ToSkillZoneForm(BaseModelForm):
    verbose_name = _("Add To Skill Zone")
    skill_zone_ids = forms.ModelMultipleChoiceField(
        queryset=SkillZone.objects.all(), label=_("Skill Zones")
    )

    class Meta:
        """
        Class Meta for additional options
        """

        model = SkillZoneCandidate
        fields = "__all__"
        exclude = [
            "skill_zone_id",
            "is_active",
            "candidate_id",
        ]
        error_messages = {
            NON_FIELD_ERRORS: {
                "unique_together": "This candidate alreay exist in this skill zone",
            }
        }

    def clean(self):
        cleaned_data = super().clean()
        candidate = cleaned_data.get("candidate_id")
        skill_zones = cleaned_data.get("skill_zone_ids")
        skill_zone_list = []
        for skill_zone in skill_zones:
            # Check for the unique together constraint manually
            if SkillZoneCandidate.objects.filter(
                candidate_id=candidate, skill_zone_id=skill_zone
            ).exists():
                # Raise a ValidationError with a custom error message
                skill_zone_list.append(skill_zone)
        if len(skill_zone_list) > 0:
            skill_zones_str = ", ".join(
                str(skill_zone) for skill_zone in skill_zone_list
            )
            raise ValidationError(f"{candidate} already exists in {skill_zones_str}.")

            # cleaned_data['skill_zone_id'] =skill_zone
        return cleaned_data

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class RejectReasonForm(ModelForm):
    """
    RejectReasonForm
    """

    verbose_name = "Reject Reason"

    class Meta:
        model = RejectReason
        fields = "__all__"
        exclude = ["is_active"]

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class RejectedCandidateForm(ModelForm):
    """
    RejectedCandidateForm
    """

    verbose_name = "Rejected Candidate"

    class Meta:
        model = RejectedCandidate
        fields = "__all__"
        exclude = ["is_active"]

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reject_reason_id"].empty_label = None
        self.fields["candidate_id"].widget = self.fields["candidate_id"].hidden_widget()


class ScheduleInterviewForm(BaseModelForm):
    """
    ScheduleInterviewForm
    """

    class Meta:
        model = InterviewSchedule
        fields = "__all__"
        exclude = ["is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["interview_date"].widget = forms.DateInput(
            attrs={"type": "date", "class": "oh-input w-100"}
        )
        self.fields["interview_time"].widget = forms.TimeInput(
            attrs={"type": "time", "class": "oh-input w-100"}
        )

    def clean(self):

        instance = self.instance
        cleaned_data = super().clean()
        interview_date = cleaned_data.get("interview_date")
        interview_time = cleaned_data.get("interview_time")
        managers = cleaned_data["employee_id"]
        if not instance.pk and interview_date and interview_date < date.today():
            self.add_error("interview_date", _("Interview date cannot be in the past."))

        if not instance.pk and interview_time:
            now = datetime.now().time()
            if (
                not instance.pk
                and interview_date == date.today()
                and interview_time < now
            ):
                self.add_error(
                    "interview_time", _("Interview time cannot be in the past.")
                )

        if apps.is_installed("leave"):
            from leave.models import LeaveRequest

            leave_employees = LeaveRequest.objects.filter(
                employee_id__in=managers, status="approved"
            )
        else:
            leave_employees = []

        employees = [
            leave.employee_id.get_full_name()
            for leave in leave_employees
            if interview_date in leave.requested_dates()
        ]

        if employees:
            self.add_error(
                "employee_id", _(f"{employees} have approved leave on this date")
            )

        return cleaned_data

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class SkillsForm(ModelForm):
    class Meta:
        model = Skill
        fields = ["title"]


class TechnicalSkillForm(ModelForm):
    class Meta:
        model = TechnicalSkill
        fields = ["title"]


class NonTechnicalSkillForm(ModelForm):
    class Meta:
        model = NonTechnicalSkill
        fields = ["title"]


class ResumeForm(ModelForm):
    class Meta:
        model = Resume
        fields = ["file", "recruitment_id"]
        widgets = {"recruitment_id": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs.update(
            {
                "onchange": "submitForm($(this))",
            }
        )


class CandidateDocumentRequestForm(ModelForm):
    class Meta:
        model = CandidateDocumentRequest
        fields = "__all__"
        exclude = ["is_active"]


class CandidateDocumentUpdateForm(ModelForm):
    """form to Update a Document"""

    verbose_name = "CandidateDocument"

    class Meta:
        model = CandidateDocument
        fields = "__all__"
        exclude = ["is_active", "document_request_id"]


class CandidateDocumentRejectForm(ModelForm):
    """form to add rejection reason while rejecting a Document"""

    class Meta:
        model = CandidateDocument
        fields = ["reject_reason"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reject_reason"].widget.attrs["required"] = True


class CandidateDocumentForm(ModelForm):
    """form to create a new Document"""

    verbose_name = "Document"

    class Meta:
        model = CandidateDocument
        fields = "__all__"
        exclude = ["document_request_id", "status", "reject_reason", "is_active"]
        widgets = {
            "employee_id": forms.HiddenInput(),
        }

    def as_p(self):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


# CandidateApplication Forms

class CandidateApplicationCreationForm(BaseModelForm):
    """
    Form for creating CandidateApplication instances
    """
    verbose_name = "Candidate Application"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recruitment_id"].empty_label = None
        if instance := kwargs.get("instance"):
            self.verbose_name = instance.name

    def save(self, commit: bool = True):
        candidate_app = self.instance
        recruitment = candidate_app.recruitment_id
        stage = candidate_app.stage_id
        candidate_app.hired = False
        candidate_app.start_onboard = False
        if stage is not None:
            if stage.stage_type == "selected" and candidate_app.canceled is False:
                candidate_app.hired = True
                candidate_app.start_onboard = True
        candidate_app.recruitment_id = recruitment
        candidate_app.stage_id = stage
        job_id = self.data.get("job_position_id")
        if job_id:
            job_position = JobPosition.objects.get(id=job_id)
            self.instance.job_position_id = job_position
        return super().save(commit)

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string(
            "candidate_application/candidate_application_create_form_as_p.html", context
        )
        return table_html

    class Meta:
        model = CandidateApplication
        fields = "__all__"
        exclude = [
            "is_active",
            "sequence",
            "hired_date",
            "probation_end",
            "offer_letter_status",
            "converted",
            "start_onboard",
            "hired",
            "canceled",
            "converted_employee_id",
            "last_updated",
        ]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "joining_date": forms.DateInput(attrs={"type": "date"}),
            "schedule_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class SimpleCandidateApplicationForm(forms.Form):
    """
    Simplified form for creating candidate applications with three fields:
    1. Candidate multi-select (from existing candidates)
    2. Recruitment single-select
    3. Job Position single-select (filtered by recruitment)
    """
    verbose_name = "Create Candidate Application"
    
    candidates = HorillaMultiSelectField(
        queryset=Candidate.objects.filter(is_active=True),
        widget=HorillaMultiSelectWidget(
            filter_route_name="candidate-filter",
            filter_class=None,
            filter_instance_contex_name="f",
            filter_context_name="candidate_filter",
        ),
        label=_("Select Candidates"),
        help_text=_("Choose one or more candidates to create applications for"),
    )
    
    recruitment = forms.ModelChoiceField(
        queryset=Recruitment.objects.filter(is_active=True, closed=False),
        label=_("Recruitment"),
        help_text=_("Select the recruitment to create applications for"),
        widget=forms.Select(attrs={"class": "oh-select oh-select-2 select2-hidden-accessible"}),
    )
    
    job_position = forms.ModelChoiceField(
        queryset=JobPosition.objects.all(),
        label=_("Job Position"),
        help_text=_("Select the specific job position for this application"),
        widget=forms.Select(attrs={"class": "oh-select oh-select-2 select2-hidden-accessible"}),
        required=True,
    )
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # Set up the recruitment field to show only active recruitments
        self.fields['recruitment'].queryset = Recruitment.objects.filter(
            is_active=True, 
            closed=False
        ).order_by('title')
        
        # Set up the candidates field to show only active candidates
        self.fields['candidates'].queryset = Candidate.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Set up the job position field - will be filtered by JavaScript
        self.fields['job_position'].queryset = JobPosition.objects.all().order_by('job_position')
        
        # Apply consistent styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select,)):
                field.widget.attrs.update({
                    "class": "oh-select oh-select-2 select2-hidden-accessible"
                })
        
        # Add JavaScript for dynamic job position filtering
        self.fields['recruitment'].widget.attrs.update({
            "onchange": "filterJobPositions(this.value)",
            "data-job-positions-url": "/recruitment/get-job-positions/"
        })
        
        # Add JavaScript function to filter job positions
        self.fields['job_position'].widget.attrs.update({
            "id": "id_job_position"
        })
        
        # Set initial values if instance is provided
        if self.instance:
            # Find the candidate based on email match and set as initial value
            if self.instance.email:
                try:
                    candidate = Candidate.objects.get(email=self.instance.email)
                    # Set the initial value for the candidates field
                    self.initial['candidates'] = [candidate]
                except Candidate.DoesNotExist:
                    pass
            
            if self.instance.recruitment_id:
                self.initial['recruitment'] = self.instance.recruitment_id.id
                # Also set the field's initial value directly
                self.fields['recruitment'].initial = self.instance.recruitment_id.id
            
            if self.instance.job_position_id:
                self.initial['job_position'] = self.instance.job_position_id.id
                # Also set the field's initial value directly
                self.fields['job_position'].initial = self.instance.job_position_id.id
                
                # Ensure the job position is in the queryset for the disabled field
                if self.instance.job_position_id not in self.fields['job_position'].queryset:
                    self.fields['job_position'].queryset = JobPosition.objects.filter(
                        id=self.instance.job_position_id.id
                    ).union(self.fields['job_position'].queryset)
                
                # Set the widget's initial value explicitly
                self.fields['job_position'].widget.attrs['data-initial-value'] = str(self.instance.job_position_id.id)
                # Also set the value attribute directly
                self.fields['job_position'].widget.attrs['value'] = str(self.instance.job_position_id.id)
            
            # Add hidden fields to preserve the values when form is submitted
            self.fields['recruitment_hidden'] = forms.CharField(
                widget=forms.HiddenInput(),
                initial=self.instance.recruitment_id.id if self.instance.recruitment_id else None
            )
            self.fields['job_position_hidden'] = forms.CharField(
                widget=forms.HiddenInput(),
                initial=self.instance.job_position_id.id if self.instance.job_position_id else None
            )
            
            # Make recruitment and job_position readonly for update form
            self.fields['recruitment'].widget.attrs.update({
                "disabled": "disabled",
                "readonly": "readonly"
            })
            self.fields['job_position'].widget.attrs.update({
                "disabled": "disabled", 
                "readonly": "readonly"
            })
    
    def clean(self):
        """
        Custom validation for the form
        """
        cleaned_data = super().clean()
        candidates = cleaned_data.get('candidates')
        recruitment = cleaned_data.get('recruitment')
        job_position = cleaned_data.get('job_position')
        
        # For update form, use hidden field values if main fields are disabled
        if self.instance:
            if not recruitment and 'recruitment_hidden' in cleaned_data:
                recruitment_id = cleaned_data.get('recruitment_hidden')
                if recruitment_id:
                    try:
                        recruitment = Recruitment.objects.get(id=recruitment_id)
                        cleaned_data['recruitment'] = recruitment
                    except Recruitment.DoesNotExist:
                        pass
            
            if not job_position and 'job_position_hidden' in cleaned_data:
                job_position_id = cleaned_data.get('job_position_hidden')
                if job_position_id:
                    try:
                        job_position = JobPosition.objects.get(id=job_position_id)
                        cleaned_data['job_position'] = job_position
                    except JobPosition.DoesNotExist:
                        pass
        
        # Handle HorillaMultiSelectField validation
        if isinstance(self.fields.get('candidates'), HorillaMultiSelectField):
            ids = self.data.getlist('candidates')
            if ids:
                self.errors.pop('candidates', None)
                # Re-validate the field with the IDs
                try:
                    candidates = self.fields['candidates'].to_python(ids)
                    cleaned_data['candidates'] = candidates
                except forms.ValidationError as e:
                    self.add_error('candidates', e)
        
        if not candidates:
            raise forms.ValidationError(_("Please select at least one candidate."))
        
        if not recruitment:
            raise forms.ValidationError(_("Please select a recruitment."))
        
        if not job_position:
            raise forms.ValidationError(_("Please select a job position."))
        
        return cleaned_data
    
    def save(self):
        """
        Update the CandidateApplication instance
        """
        candidates = self.cleaned_data['candidates']
        recruitment = self.cleaned_data['recruitment']
        job_position = self.cleaned_data['job_position']
        
        if self.instance and candidates:
            # For update, we only use the first candidate (since it's a single application)
            candidate = candidates[0]
            
            # Update the existing application
            self.instance.recruitment_id = recruitment
            self.instance.job_position_id = job_position
            
            # Update candidate data from the selected candidate
            self.instance.name = candidate.name
            self.instance.email = candidate.email
            self.instance.mobile = candidate.mobile
            self.instance.profile = candidate.profile
            self.instance.resume = candidate.resume
            self.instance.portfolio = candidate.portfolio
            self.instance.address = candidate.address
            self.instance.country = candidate.country
            self.instance.state = candidate.state
            self.instance.city = candidate.city
            self.instance.zip = candidate.zip
            self.instance.gender = candidate.gender
            self.instance.dob = candidate.dob
            
            self.instance.save()
            return [self.instance]
        
        return []


class CandidateApplicationDropDownForm(BaseModelForm):
    """
    Form for CandidateApplication dropdown functionality
    """
    
    class Meta:
        model = CandidateApplication
        fields = [
            "name",
            "email",
            "mobile",
            "recruitment_id",
            "stage_id",
            "resume",
            "job_position_id",
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recruitment_id"].empty_label = None


class StageNoteApplicationForm(ModelForm):
    """
    Form for creating StageNoteApplication instances
    """
    verbose_name = "Stage Note Application"
    
    class Meta:
        model = StageNoteApplication
        fields = "__all__"
        exclude = ["is_active", "updated_by", "stage_id", "candidate_application_id"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        files = []
        for key, file in self.files.items():
            if key.startswith("attachment"):
                stage_file = StageFiles()
                stage_file.files = file
                stage_file.save()
                files.append(stage_file.id)
        
        note = super().save(commit=False)
        if commit:
            note.save()
        return note, files


class InterviewScheduleApplicationForm(ModelForm):
    """
    Form for creating InterviewScheduleApplication instances
    """
    verbose_name = "Interview Schedule Application"
    
    class Meta:
        model = InterviewScheduleApplication
        fields = "__all__"
        exclude = ["is_active", "candidate_application_id"]
        widgets = {
            "interview_date": forms.DateInput(attrs={"type": "date"}),
            "interview_time": forms.TimeInput(attrs={"type": "time"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ApplicationForm(ModelForm):
    """
    Application form for candidates to apply through CandidateApplication
    """
    def __init__(self, recruitment=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if recruitment:
            self.instance.recruitment_id = recruitment
            # Set stage to sourced stage
            sourced_stage = Stage.objects.filter(
                recruitment_id=recruitment, stage_type="sourced"
            ).first()
            if sourced_stage:
                self.instance.stage_id = sourced_stage

    class Meta:
        model = CandidateApplication
        fields = [
            "name",
            "email", 
            "mobile",
            "resume",
            "portfolio",
            "address",
            "country",
            "state",
            "city",
            "zip",
            "gender",
            "dob",
            "profile"
        ]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "gender": forms.Select(),
            "address": forms.Textarea(attrs={"rows": 3}),
        }


class CandidateApplicationUpdateForm(BaseModelForm):
    """
    Form for updating CandidateApplication instances
    """
    verbose_name = "Update Candidate Application"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent styling
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.DateInput)):
                field.initial = date.today()

            if isinstance(
                widget,
                (forms.NumberInput, forms.EmailInput, forms.TextInput, forms.FileInput),
            ):
                label = _(field.label)
                field.widget.attrs.update(
                    {"class": "oh-input w-100", "placeholder": label}
                )
            elif isinstance(widget, (forms.Select,)):
                label = ""
                if field.label is not None:
                    label = _(field.label)
                field.empty_label = _(f"---Choose {label}---")
                field.widget.attrs.update(
                    {"class": "oh-select oh-select-2 select2-hidden-accessible"}
                )
            elif isinstance(widget, (forms.Textarea)):
                if field.label is not None:
                    label = _(field.label)
                field.widget.attrs.update(
                    {
                        "class": "oh-input w-100",
                        "placeholder": label,
                        "rows": 2,
                        "cols": 40,
                    }
                )

    class Meta:
        model = CandidateApplication
        fields = "__all__"
        exclude = [
            "is_active",
            "sequence", 
            "hired_date",
            "probation_end",
            "offer_letter_status",
            "last_updated",
        ]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "joining_date": forms.DateInput(attrs={"type": "date"}),
            "schedule_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class CandidateApplicationStageUpdateForm(ModelForm):
    """
    Form for updating stage of CandidateApplication
    """
    
    class Meta:
        model = CandidateApplication
        fields = ["stage_id", "schedule_date"]
        widgets = {
            "schedule_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if instance := kwargs.get("instance"):
            # Filter stages to current recruitment only
            self.fields["stage_id"].queryset = Stage.objects.filter(
                recruitment_id=instance.recruitment_id
            )


class ToSkillZoneApplicationForm(forms.Form):
    """
    Form to add CandidateApplication to skill zones
    """
    skill_zone_ids = HorillaMultiSelectField(
        queryset=SkillZone.objects.filter(is_active=True),
        widget=HorillaMultiSelectWidget(
            filter_route_name="skill-zone-filter",
            filter_class=None,
            filter_instance_contex_name="f",
            filter_context_name="skill_zone_filter",
        ),
        label=_("Skill Zone"),
    )
    reason = forms.CharField(
        max_length=200,
        widget=forms.Textarea(attrs={"rows": 3}),
        label=_("Reason")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


# Document Management Forms for CandidateApplication

class CandidateApplicationDocumentForm(ModelForm):
    """
    Form for CandidateApplication document management
    """
    
    class Meta:
        model = CandidateDocument  # Reusing existing model but will link to CandidateApplication
        fields = ["title", "document", "status", "reject_reason"]
        widgets = {
            "reject_reason": forms.Textarea(attrs={"rows": 3}),
        }


class CandidateApplicationDocumentUpdateForm(ModelForm):
    """
    Form for updating CandidateApplication documents
    """
    
    class Meta:
        model = CandidateDocument
        fields = ["document"]


class CandidateApplicationConversionForm(forms.Form):
    """
    Form for converting CandidateApplication to Employee
    """
    confirm_conversion = forms.BooleanField(
        required=True,
        label=_("I confirm this candidate application should be converted to an employee")
    )
    
    def __init__(self, candidate_application=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidate_application = candidate_application


class CandidateWorkExperienceForm(BaseModelForm):
    """
    Form for candidate work experience
    """
    
    class Meta:
        model = CandidateWorkExperience
        fields = [
            'company_name', 'company_website', 'company_location',
            'job_title', 'department', 'start_date', 'end_date',
            'is_current', 'job_description', 'achievements',
            'employment_type', 'salary', 'currency'
        ]
        widgets = {
            'company_name': forms.TextInput(),
            'company_website': forms.URLInput(),
            'company_location': forms.TextInput(),
            'job_title': forms.TextInput(),
            'department': forms.TextInput(),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'is_current': forms.CheckboxInput(),
            'job_description': forms.Textarea(attrs={'rows': 4}),
            'achievements': forms.Textarea(attrs={'rows': 4}),
            'employment_type': forms.Select(),
            'salary': forms.NumberInput(),
            'currency': forms.TextInput(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_current = cleaned_data.get('is_current')
        
        if not is_current and start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_("Start date cannot be after end date."))
        
        return cleaned_data


class CandidateWorkProjectForm(BaseModelForm):
    """
    Form for candidate work projects
    """
    
    class Meta:
        model = CandidateWorkProject
        fields = [
            'project_name', 'project_description', 'technologies_used',
            'project_url', 'start_date', 'end_date', 'is_current', 'role'
        ]
        widgets = {
            'project_name': forms.TextInput(),
            'project_description': forms.Textarea(attrs={'rows': 4}),
            'technologies_used': forms.Textarea(attrs={'rows': 3}),
            'project_url': forms.URLInput(),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'is_current': forms.CheckboxInput(),
            'role': forms.TextInput(),
        }


class CandidateEducationForm(BaseModelForm):
    """
    Form for candidate education
    """
    
    class Meta:
        model = CandidateEducation
        fields = [
            'institution_name', 'institution_location', 'institution_website',
            'degree_name', 'field_of_study', 'start_date', 'end_date',
            'graduation_date', 'is_current', 'gpa', 'max_gpa',
            'honors', 'activities', 'description'
        ]
        widgets = {
            'institution_name': forms.TextInput(),
            'institution_location': forms.TextInput(),
            'institution_website': forms.URLInput(),
            'degree_name': forms.TextInput(),
            'field_of_study': forms.TextInput(),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'graduation_date': forms.DateInput(attrs={'type': 'date'}),
            'is_current': forms.CheckboxInput(),
            'gpa': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '4'}),
            'max_gpa': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '4'}),
            'honors': forms.Textarea(attrs={'rows': 3}),
            'activities': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        gpa = cleaned_data.get('gpa')
        max_gpa = cleaned_data.get('max_gpa')
        
        if gpa and max_gpa and gpa > max_gpa:
            raise forms.ValidationError(_("GPA cannot be higher than maximum GPA."))
        
        return cleaned_data


class CandidateCertificationForm(BaseModelForm):
    """
    Form for candidate certifications
    """
    
    class Meta:
        model = CandidateCertification
        fields = [
            'certification_name', 'issuing_organization', 'organization_website',
            'issue_date', 'expiry_date', 'is_current', 'credential_id',
            'credential_url', 'description', 'skills_covered'
        ]
        widgets = {
            'certification_name': forms.TextInput(),
            'issuing_organization': forms.TextInput(),
            'organization_website': forms.URLInput(),
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'is_current': forms.CheckboxInput(),
            'credential_id': forms.TextInput(),
            'credential_url': forms.URLInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'skills_covered': forms.Textarea(attrs={'rows': 3}),
        }


class CandidateSkillForm(BaseModelForm):
    """
    Form for candidate skills
    """
    verbose_name = _("Candidate Skill")
    
    class Meta:
        model = CandidateSkill
        fields = [
            'skill_name', 'proficiency_level', 'years_of_experience', 'relevant_years_of_experience'
        ]
        widgets = {
            'skill_name': forms.TextInput(),
            'proficiency_level': forms.Select(),
            'years_of_experience': forms.NumberInput(attrs={'min': '0'}),
            'relevant_years_of_experience': forms.NumberInput(attrs={'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['skill_name'].widget.attrs.update({'placeholder': _('Enter skill name')})
        
        # Ensure proficiency_level choices are properly set
        self.fields['proficiency_level'].choices = [
            ("beginner", _("Beginner")),
            ("intermediate", _("Intermediate")),
            ("advanced", _("Advanced")),
            ("expert", _("Expert")),
        ]
    
    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html
    
    def save(self, commit=True):
        """
        Save the form
        """
        return super().save(commit)


class CandidateSkillRatingForm(BaseModelForm):
    """
    Form for candidate skill ratings
    """
    verbose_name = _("Skill Rating")
    
    class Meta:
        model = CandidateSkillRating
        fields = [
            'recruitment', 'stage', 'skill_name', 'skill_category', 'rating', 'notes'
        ]
        widgets = {
            'recruitment': forms.Select(attrs={'class': 'form-control'}),
            'stage': forms.Select(attrs={'class': 'form-control'}),
            'skill_name': forms.TextInput(attrs={'class': 'form-control'}),
            'skill_category': forms.Select(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.0',
                'max': '5.0',
                'step': '0.1',
                'placeholder': '0.0 - 5.0'
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['skill_name'].widget.attrs.update({'placeholder': _('Enter skill name')})
        self.fields['notes'].widget.attrs.update({'placeholder': _('Add notes about the rating')})
        
        # Make recruitment and stage required only if not provided in initial data
        if not self.initial.get('recruitment'):
            self.fields['recruitment'].required = True
        else:
            self.fields['recruitment'].required = False
            self.fields['recruitment'].widget = forms.HiddenInput()
            
        if not self.initial.get('stage'):
            self.fields['stage'].required = True
        else:
            self.fields['stage'].required = False
            self.fields['stage'].widget = forms.HiddenInput()
    
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is not None:
            if rating < 0.0 or rating > 5.0:
                raise ValidationError(_("Rating must be between 0.0 and 5.0"))
        return rating
    
    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


# Inline FormSets for Dynamic Addition/Deletion
CandidateWorkExperienceFormSet = inlineformset_factory(
    Candidate,
    CandidateWorkExperience,
    form=CandidateWorkExperienceForm,
    extra=1,
    can_delete=True,
    fields=[
        'company_name', 'company_website', 'company_location',
        'job_title', 'department', 'start_date', 'end_date',
        'is_current', 'job_description', 'achievements',
        'employment_type', 'salary', 'currency'
    ]
)

CandidateWorkProjectFormSet = inlineformset_factory(
    CandidateWorkExperience,
    CandidateWorkProject,
    form=CandidateWorkProjectForm,
    extra=1,
    can_delete=True,
    fields=[
        'project_name', 'project_description', 'technologies_used',
        'project_url', 'start_date', 'end_date', 'is_current', 'role'
    ]
)

CandidateEducationFormSet = inlineformset_factory(
    Candidate,
    CandidateEducation,
    form=CandidateEducationForm,
    extra=1,
    can_delete=True,
    fields=[
        'institution_name', 'institution_location', 'institution_website',
        'degree_name', 'field_of_study', 'start_date', 'end_date',
        'graduation_date', 'is_current', 'gpa', 'max_gpa',
        'honors', 'activities', 'description'
    ]
)

CandidateCertificationFormSet = inlineformset_factory(
    Candidate,
    CandidateCertification,
    form=CandidateCertificationForm,
    extra=1,
    can_delete=True,
    fields=[
        'certification_name', 'issuing_organization', 'organization_website',
        'issue_date', 'expiry_date', 'is_current', 'credential_id',
        'credential_url', 'description', 'skills_covered'
    ]
)

CandidateSkillFormSet = inlineformset_factory(
    Candidate,
    CandidateSkill,
    form=CandidateSkillForm,
    extra=1,
    can_delete=True,
    fields=[
        'skill_name', 'proficiency_level', 'years_of_experience', 'relevant_years_of_experience'
    ]
)





class LinkedInAccountForm(BaseModelForm):
    """
    Form for LinkedIn Account model
    """
    verbose_name = _("LinkedIn Account")

    class Meta:
        model = LinkedInAccount
        fields = [
            'username', 'email', 'api_token', 'company_id'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'oh-input w-100',
                'placeholder': _('LinkedIn Username')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'oh-input w-100',
                'placeholder': _('LinkedIn Email')
            }),
            'api_token': forms.TextInput(attrs={
                'class': 'oh-input w-100',
                'placeholder': _('LinkedIn API Token'),
                'type': 'password'
            }),
            'company_id': forms.Select(attrs={
                'class': 'oh-select oh-select-2'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_id'].queryset = Company.objects.filter(is_active=True)

    def as_p(self, *args, **kwargs):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class SimpleCandidateApplicationUpdateForm(forms.Form):
    """
    Simplified form for updating candidate applications with three fields:
    1. Candidate multi-select (from existing candidates) - same as create form
    2. Recruitment text input (readonly in update)
    3. Job Position text input (readonly in update)
    """
    verbose_name = "Update Candidate Application"
    
    candidates = HorillaMultiSelectField(
        queryset=Candidate.objects.filter(is_active=True),
        widget=HorillaMultiSelectWidget(
            filter_route_name="candidate-filter",
            filter_class=None,
            filter_instance_contex_name="f",
            filter_context_name="candidate_filter",
        ),
        label=_("Select Candidates"),
        help_text=_("Choose the candidate for this application"),
    )
    
    recruitment = forms.CharField(
        label=_("Recruitment"),
        help_text=_("Recruitment for this application"),
        widget=forms.TextInput(attrs={"class": "oh-input w-100", "readonly": "readonly"}),
        required=False,
    )
    
    job_position = forms.CharField(
        label=_("Job Position"),
        help_text=_("Job position for this application"),
        widget=forms.TextInput(attrs={"class": "oh-input w-100", "readonly": "readonly"}),
        required=False,
    )
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # Set up the candidates field to show only active candidates
        self.fields['candidates'].queryset = Candidate.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Set initial values if instance is provided
        if self.instance:
            # Find the candidate based on email match and set as initial value
            if self.instance.email:
                try:
                    candidate = Candidate.objects.get(email=self.instance.email)
                    # Set the initial value for the candidates field
                    self.initial['candidates'] = [candidate]
                except Candidate.DoesNotExist:
                    pass
            
            # Set recruitment and job position as text values
            if self.instance.recruitment_id:
                self.initial['recruitment'] = self.instance.recruitment_id.title
            
            if self.instance.job_position_id:
                self.initial['job_position'] = self.instance.job_position_id.job_position
            
            # Add hidden fields to preserve the values when form is submitted
            self.fields['recruitment_hidden'] = forms.CharField(
                widget=forms.HiddenInput(),
                initial=self.instance.recruitment_id.id if self.instance.recruitment_id else None
            )
            self.fields['job_position_hidden'] = forms.CharField(
                widget=forms.HiddenInput(),
                initial=self.instance.job_position_id.id if self.instance.job_position_id else None
            )
    
    def clean(self):
        """
        Custom validation for the form
        """
        cleaned_data = super().clean()
        candidates = cleaned_data.get('candidates')
        recruitment = cleaned_data.get('recruitment')
        job_position = cleaned_data.get('job_position')
        
        # For update form, use hidden field values
        if self.instance:
            if 'recruitment_hidden' in cleaned_data:
                recruitment_id = cleaned_data.get('recruitment_hidden')
                if recruitment_id:
                    try:
                        recruitment = Recruitment.objects.get(id=recruitment_id)
                        cleaned_data['recruitment'] = recruitment
                    except Recruitment.DoesNotExist:
                        pass
            
            if 'job_position_hidden' in cleaned_data:
                job_position_id = cleaned_data.get('job_position_hidden')
                if job_position_id:
                    try:
                        job_position = JobPosition.objects.get(id=job_position_id)
                        cleaned_data['job_position'] = job_position
                    except JobPosition.DoesNotExist:
                        pass
        
        # Handle HorillaMultiSelectField validation
        if isinstance(self.fields.get('candidates'), HorillaMultiSelectField):
            ids = self.data.getlist('candidates')
            if ids:
                self.errors.pop('candidates', None)
                # Re-validate the field with the IDs
                try:
                    candidates = self.fields['candidates'].to_python(ids)
                    cleaned_data['candidates'] = candidates
                except forms.ValidationError as e:
                    self.add_error('candidates', e)
        
        if not candidates:
            raise forms.ValidationError(_("Please select at least one candidate."))
        
        if not recruitment:
            raise forms.ValidationError(_("Please select a recruitment."))
        
        if not job_position:
            raise forms.ValidationError(_("Please select a job position."))
        
        return cleaned_data
    
    def save(self):
        """
        Update the CandidateApplication instance
        """
        candidates = self.cleaned_data['candidates']
        recruitment = self.cleaned_data['recruitment']
        job_position = self.cleaned_data['job_position']
        
        if self.instance and candidates:
            # For update, we only use the first candidate (since it's a single application)
            candidate = candidates[0]
            
            # Update the existing application
            self.instance.recruitment_id = recruitment
            self.instance.job_position_id = job_position
            
            # Update candidate data from the selected candidate
            self.instance.name = candidate.name
            self.instance.email = candidate.email
            self.instance.mobile = candidate.mobile
            self.instance.profile = candidate.profile
            self.instance.resume = candidate.resume
            self.instance.portfolio = candidate.portfolio
            self.instance.address = candidate.address
            self.instance.country = candidate.country
            self.instance.state = candidate.state
            self.instance.city = candidate.city
            self.instance.zip = candidate.zip
            self.instance.gender = candidate.gender
            self.instance.dob = candidate.dob
            
            self.instance.save()
            return [self.instance]
        
        return []
