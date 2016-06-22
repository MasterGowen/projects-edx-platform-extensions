"""
Management command to rename projects app to edx_solutions_projects
"""
import logging
from south.db import db
from django.core.management.base import BaseCommand

log = logging.getLogger(__name__)


def get_table_names():
    """
    Returns list of table name projects app has
    """
    return [
        'peerreview',
        'project',
        'project_workgroups',
        'submission',
        'submissionreview',
        'workgroup',
        'workgroup_groups',
        'workgrouppeerreview',
        'workgroupreview',
        'workgroupsubmission',
        'workgroupsubmissionreview',
        'workgroup_users',
    ]


class Command(BaseCommand):
    """
    Renames projects app to edx_solutions_projects and updates database accordingly
    """
    help = 'Makes database level changes to renames projects app to edx_solutions_projects'
    old_appname = 'projects'
    new_appname = 'edx_solutions_projects'

    def handle(self, *args, **options):
        log.info('renaming projects app and related tables')
        db.execute(
            "UPDATE south_migrationhistory SET app_name = %s WHERE app_name = %s", [self.new_appname, self.old_appname]
        )
        db.execute(
            "UPDATE django_content_type SET app_label = %s WHERE app_label = %s", [self.new_appname, self.old_appname]
        )

        for table_name in get_table_names():
            db.rename_table(
                '{old_app}_{table_name}'.format(old_app=self.old_appname, table_name=table_name),
                '{new_app}_{table_name}'.format(new_app=self.new_appname, table_name=table_name),
            )

        log.info('projects app and related tables successfully renamed')