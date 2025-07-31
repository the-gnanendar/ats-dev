"""
recruitmentfilters.py

This module is used to write custom template filters.

"""

import json
import uuid

from django import template
from django.apps import apps
from django.contrib.auth.models import User
from django.template.defaultfilters import register

from recruitment.models import CandidateRating

# from django.forms.boundfield

register = template.Library()


@register.filter(name="is_stagemanager")
def is_stagemanager(user):
    """
    This method is used to check the employee is stage or recruitment manager
    """
    try:
        employee_obj = user.employee_get
        return (
            employee_obj.stage_set.all().exists()
            or employee_obj.recruitment_set.exists()
        )
    except Exception:
        return False


@register.filter(name="is_recruitmentmanager")
def is_recruitmentmangers(user):
    """
    This method is used to check the employee is recruitment manager
    """
    try:
        employee_obj = user.employee_get
        return employee_obj.recruitment_set.exists()
    except Exception:
        return False


@register.filter(name="stage_manages")
def stage_manages(user, recruitment):
    """
    This method is used to check the employee is manager in any stage in a recruitment
    """
    try:
        return (
            recruitment.stage_set.filter(stage_managers=user.employee_get).exists()
            or recruitment.recruitment_managers.filter(id=user.employee_get.id).exists()
        )
    except Exception as _:
        return False


@register.filter(name="recruitment_manages")
def recruitment_manages(user, recruitment):
    """
    This method is used to check the employee in recruitment managers
    """
    try:
        employee_obj = user.employee_get
        return recruitment.recruitment_managers.filter(id=employee_obj.id).exists()
    except Exception:
        return False


@register.filter(name="employee")
def employee(uid):
    """
    This method is used to return user object with the arg id.

    Args:
        uid (int): user object id

    Returns:
        user object
    """
    return User.objects.get(id=uid).employee_get if uid is not None else None


@register.filter(name="media_path")
def media_path(form_tag):
    """
    This method will returns the path of media
    """
    return form_tag.subwidgets[0].__dict__["data"]["value"]


@register.filter(name="generate_id")
def generate_id(element, label=""):
    """
    This method is used to generate element id attr
    """
    element.field.widget.attrs.update({"id": label + str(uuid.uuid1())})
    return element


@register.filter(name="has_candidate_rating")
def has_candidate_rating(candidate_ratings, cand):
    candidate_rating = candidate_ratings.filter(candidate_id=cand.id).first()
    return candidate_rating


@register.filter(name="rating")
def rating(candidate_ratings, cand):
    rating = candidate_ratings.filter(candidate_id=cand.id).first().rating
    return str(rating)


@register.filter(name="avg_rating")
def avg_rating(candidate_ratings, cand):
    ratings = CandidateRating.objects.filter(candidate_id=cand.id)
    rating_list = []
    avg_rate = 0
    for rating in ratings:
        rating_list.append(rating.rating)
    if len(rating_list) != 0:
        avg_rate = round(sum(rating_list) / len(rating_list))

    return str(avg_rate)


@register.filter(name="percentage")
def percentage(value, total):
    if total == 0 or not total:
        return 0
    return min(round((value / total) * 100, 2), 100)


@register.filter(name="is_in_task_managers")
def is_in_task_managers(user):
    """
    This method is used to check the user in the task manager or not
    """
    if apps.is_installed("onboarding"):
        from onboarding.models import OnboardingTask

        return OnboardingTask.objects.filter(
            employee_id__employee_user_id=user
        ).exists()
    return False


@register.filter(name="pipeline_grouper")
def pipeline_grouper(grouper: dict = {}):
    """
    This method is used itemize the dictionary
    """
    return grouper["title"], grouper["stages"]


@register.filter(name="to_json")
def to_json(value):
    ordered_list = [
        {"id": val.id, "stage": val.stage, "type": val.stage_type} for val in value
    ]
    return json.dumps(ordered_list)


@register.filter(name="skills_by_proficiency")
def skills_by_proficiency(skills, proficiency_level):
    """
    Filter skills by proficiency level
    """
    return skills.filter(proficiency_level=proficiency_level).count()


@register.filter(name="skills_by_highlighted")
def skills_by_highlighted(skills):
    """
    Count highlighted skills
    """
    return skills.filter(is_highlighted=True).count()


@register.filter(name="get_process_status")
def get_process_status(application):
    """
    Get the process status based on stage type and application status
    """
    if application.canceled:
        return "cancelled"
    elif application.converted:
        return "converted"
    elif application.hired:
        return "hired"
    elif application.stage_id:
        stage_type = application.stage_id.stage_type
        if stage_type == "selected":
            return "selected"
        elif stage_type == "rejected":
            return "rejected"
        elif stage_type in ["l1_interview", "l2_interview", "l3_interview", "interview"]:
            return "interviewing"
        elif stage_type == "test":
            return "testing"
        elif stage_type == "shortlisted":
            return "shortlisted"
        elif stage_type == "sourced":
            return "processing"
        elif stage_type == "on-hold":
            return "on-hold"
        else:
            return "processing"
    else:
        return "processing"


@register.filter(name="get_status_badge_class")
def get_status_badge_class(status):
    """
    Get the appropriate badge class for the status
    """
    status_classes = {
        "processing": "oh-badge--info",
        "shortlisted": "oh-badge--primary", 
        "interviewing": "oh-badge--warning",
        "testing": "oh-badge--warning",
        "selected": "oh-badge--success",
        "rejected": "oh-badge--danger",
        "hired": "oh-badge--success",
        "converted": "oh-badge--primary",
        "cancelled": "oh-badge--danger",
        "on-hold": "oh-badge--secondary",
    }
    return status_classes.get(status, "oh-badge--secondary")


@register.filter(name="count_applications_by_status")
def count_applications_by_status(applications, status_type):
    """
    Count applications by status type
    """
    count = 0
    for application in applications:
        status = get_process_status(application)
        if status == status_type:
            count += 1
    return count


@register.filter(name="count_applications_by_stage_type")
def count_applications_by_stage_type(applications, stage_type):
    """
    Count applications by stage type
    """
    count = 0
    for application in applications:
        if application.stage_id and application.stage_id.stage_type == stage_type:
            count += 1
    return count


@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    Get item from dictionary by key
    """
    return dictionary.get(key)
