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
        # Use the create_default_stages method to ensure proper stage managers and interviewers
        instance.create_default_stages()


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
