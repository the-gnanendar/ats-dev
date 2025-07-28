from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from recruitment.models import (
    CandidateDocument,
    CandidateDocumentRequest,
    Recruitment,
    Stage,
)


@receiver(post_save, sender=Recruitment)
def create_initial_stage(sender, instance, created, **kwargs):
    """
    This is post save method, used to create initial stage for the recruitment
    """
    if created:
        # Create Sourced stage (combination of Initial and Applied)
        sourced_stage = Stage()
        sourced_stage.sequence = 1
        sourced_stage.recruitment_id = instance
        sourced_stage.stage = "Sourced"
        sourced_stage.stage_type = "sourced"
        sourced_stage.save()

        # Create Shortlisted stage
        shortlisted_stage = Stage()
        shortlisted_stage.sequence = 2
        shortlisted_stage.recruitment_id = instance
        shortlisted_stage.stage = "Shortlisted"
        shortlisted_stage.stage_type = "shortlisted"
        shortlisted_stage.save()

        # Create Test stage
        test_stage = Stage()
        test_stage.sequence = 3
        test_stage.recruitment_id = instance
        test_stage.stage = "Test"
        test_stage.stage_type = "test"
        test_stage.save()

        # Create Interview stage
        interview_stage = Stage()
        interview_stage.sequence = 4
        interview_stage.recruitment_id = instance
        interview_stage.stage = "Interview"
        interview_stage.stage_type = "interview"
        interview_stage.save()

        # Create Selected stage
        selected_stage = Stage()
        selected_stage.sequence = 5
        selected_stage.recruitment_id = instance
        selected_stage.stage = "Selected"
        selected_stage.stage_type = "selected"
        selected_stage.save()

        # Create Rejected stage
        rejected_stage = Stage()
        rejected_stage.sequence = 6
        rejected_stage.recruitment_id = instance
        rejected_stage.stage = "Rejected"
        rejected_stage.stage_type = "rejected"
        rejected_stage.save()

        # Create On Hold stage
        on_hold_stage = Stage()
        on_hold_stage.sequence = 7
        on_hold_stage.recruitment_id = instance
        on_hold_stage.stage = "On Hold"
        on_hold_stage.stage_type = "on-hold"
        on_hold_stage.save()

        # Create Cancelled stage
        cancelled_stage = Stage()
        cancelled_stage.sequence = 8
        cancelled_stage.recruitment_id = instance
        cancelled_stage.stage = "Cancelled"
        cancelled_stage.stage_type = "cancelled"
        cancelled_stage.save()


@receiver(m2m_changed, sender=CandidateDocumentRequest.candidate_id.through)
def document_request_m2m_changed(sender, instance, action, **kwargs):
    if action == "post_add":
        candidate_document_create(instance)

    elif action == "post_remove":
        candidate_document_create(instance)


def candidate_document_create(instance):
    candidates = instance.candidate_id.all()
    for candidate in candidates:
        document, created = CandidateDocument.objects.get_or_create(
            candidate_id=candidate,
            document_request_id=instance,
            defaults={"title": f"Upload {instance.title}"},
        )
        document.title = f"Upload {instance.title}"
        document.save()
