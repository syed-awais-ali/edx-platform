"""
One-time data migration script -- shoulen't need to run it again
"""
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from .engagement import (
    update_all_courses_engagement_scores,
    update_course_engagement_scores,
    update_user_engagement_scores
)

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Creates (or updates) social engagement entries for the specified course(s) and/or user(s)
    """

    def handle(self, *args, **options):
        help = "Command to creaete or update social engagement entries"
        option_list = BaseCommand.option_list + (
            make_option(
                "-c",
                "--course_ids",
                dest="course_ids",
                help="List of courses for which to generate social engagement",
                metavar="first/course/id,second/course/id"
            ),
            make_option(
                "-u",
                "--user_ids",
                dest="user_ids",
                help="List of users for which to generate social engagement",
                metavar="1234,2468,3579"
            ),
        )

        course_ids = options.get('course_ids')
        user_ids = options.get('user_ids')

        if course_ids:
            # over a few specific courses?
            for course_id in course_ids:
                if user_ids:
                    # over a few specific users in those courses?
                else:
                    update_course_engagement_scores(course_id, compute_if_closed_course=True)
        else:
            print 'Updating social engagement scores in all courses...'
            update_all_courses(compute_if_closed_course=True)
