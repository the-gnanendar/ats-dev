from django.core.management.base import BaseCommand
from recruitment.models import Recruitment, Stage


class Command(BaseCommand):
    help = 'Update existing stages with stage managers and interviewers from recruitment settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recruitment-id',
            type=int,
            help='Update stages for a specific recruitment ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        recruitment_id = options.get('recruitment_id')
        dry_run = options.get('dry_run')

        if recruitment_id:
            try:
                recruitment = Recruitment.objects.get(id=recruitment_id)
                self.update_recruitment_stages(recruitment, dry_run)
            except Recruitment.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Recruitment with ID {recruitment_id} does not exist')
                )
        else:
            # Update all recruitments
            recruitments = Recruitment.objects.all()
            self.stdout.write(f'Found {recruitments.count()} recruitments to process')
            
            for recruitment in recruitments:
                self.update_recruitment_stages(recruitment, dry_run)

    def update_recruitment_stages(self, recruitment, dry_run):
        """Update stages for a specific recruitment"""
        self.stdout.write(f'\nProcessing recruitment: {recruitment.title} (ID: {recruitment.id})')
        
        # Get all stages for this recruitment
        stages = Stage.objects.filter(recruitment_id=recruitment)
        
        if not stages.exists():
            self.stdout.write(self.style.WARNING('  No stages found for this recruitment'))
            return
        
        self.stdout.write(f'  Found {stages.count()} stages')
        
        updated_count = 0
        
        for stage in stages:
            stage_updated = False
            
            # Check if stage has stage managers
            if not stage.stage_managers.exists() and recruitment.default_stage_manager.exists():
                if not dry_run:
                    stage.stage_managers.set(recruitment.default_stage_manager.all())
                stage_updated = True
                self.stdout.write(f'    - Added {recruitment.default_stage_manager.count()} stage managers to "{stage.stage}"')
            
            # Check if stage has interviewers based on stage type
            if not stage.stage_interviewers.exists():
                interviewers_added = False
                
                if stage.stage_type == 'l1_interview' and recruitment.l1_interviewer.exists():
                    if not dry_run:
                        stage.stage_interviewers.set(recruitment.l1_interviewer.all())
                    self.stdout.write(f'    - Added {recruitment.l1_interviewer.count()} L1 interviewers to "{stage.stage}"')
                    interviewers_added = True
                
                elif stage.stage_type == 'l2_interview' and recruitment.l2_interviewer.exists():
                    if not dry_run:
                        stage.stage_interviewers.set(recruitment.l2_interviewer.all())
                    self.stdout.write(f'    - Added {recruitment.l2_interviewer.count()} L2 interviewers to "{stage.stage}"')
                    interviewers_added = True
                
                elif stage.stage_type == 'l3_interview' and recruitment.l3_interviewer.exists():
                    if not dry_run:
                        stage.stage_interviewers.set(recruitment.l3_interviewer.all())
                    self.stdout.write(f'    - Added {recruitment.l3_interviewer.count()} L3 interviewers to "{stage.stage}"')
                    interviewers_added = True
                
                if interviewers_added:
                    stage_updated = True
            
            if stage_updated:
                if not dry_run:
                    stage.save()
                updated_count += 1
        
        if updated_count > 0:
            if dry_run:
                self.stdout.write(self.style.SUCCESS(f'  Would update {updated_count} stages'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  Updated {updated_count} stages'))
        else:
            self.stdout.write(self.style.WARNING('  No stages needed updating')) 