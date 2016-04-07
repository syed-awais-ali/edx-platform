"""
This module has implementation of celery tasks for users' progress related use cases
"""
import logging

from celery.task import task  # pylint: disable=import-error,no-name-in-module
from django.conf import settings
from django.db.models import F, Count
from django.core.exceptions import ObjectDoesNotExist

from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import BlockUsageLocator

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from openedx.core.djangoapps.content.course_metadata.models import CourseAggregatedMetaData
from student.roles import get_aggregate_exclusion_user_ids
from progress.models import (
    CourseModuleCompletion,
    StudentProgress,
)
from gradebook.models import StudentGradebook

log = logging.getLogger('edx.celery.task')


def _get_parent_content_id(html_content_id):
    """ Gets parent block content id """
    try:
        html_usage_id = BlockUsageLocator.from_string(html_content_id)
        html_module = modulestore().get_item(html_usage_id)
        return unicode(html_module.parent)
    except (InvalidKeyError, ItemNotFoundError) as exception:
        # something has gone wrong - the best we can do is to return original content id
        log.warn("Error getting parent content_id for html module: %s", exception.message)
        return html_content_id


def _update_course_user_progress(course_id, content_id, user, created):
    """
    Updates user's progress entry
    """
    detached_categories = getattr(settings, 'PROGRESS_DETACHED_CATEGORIES', [])
    # HTML modules can be children of progress-detached and progress-included modules, so using parent id for
    # progress-detached check
    if 'html' in content_id:
        content_id = _get_parent_content_id(content_id)
    if created and not any(category in content_id for category in detached_categories):
        try:
            progress = StudentProgress.objects.get(user=user, course_id=course_id)
            progress.completions += 1
        except ObjectDoesNotExist:
            progress = StudentProgress(user=user, course_id=course_id, completions=1)
        finally:
            course_metadata = CourseAggregatedMetaData.get_from_id(course_id)
            total_possible_completions = float(course_metadata.total_assessments)
            if total_possible_completions > 0:
                completion_percentage = min(100 * (progress.completions / total_possible_completions), 100)
                progress.progress = completion_percentage
            progress.save()


# pylint: disable=invalid-name
def _update_course_metadata_aggregates(course_key):
    """
    Recalculates course metadata aggregates for users_started and modules_completed
    """
    exclude_users = get_aggregate_exclusion_user_ids(course_key)
    started = StudentProgress.objects.filter(
        course_id__exact=course_key,
        user__is_active=True,
        user__courseenrollment__is_active=True,
        user__courseenrollment__course_id__exact=course_key
    ).aggregate(Count('user', distinct=True))

    total_modules_completed = CourseModuleCompletion.get_actual_completions().filter(
        course_id__exact=course_key,
        user__courseenrollment__is_active=True,
        user__courseenrollment__course_id__exact=course_key,
        user__is_active=True
    ).exclude(user_id__in=exclude_users).count()

    grade_complete_match_range = getattr(settings, 'GRADEBOOK_GRADE_COMPLETE_PROFORMA_MATCH_RANGE', 0.01)
    total_users_completed = StudentGradebook.objects.filter(
        course_id__exact=course_key,
        user__is_active=True,
        user__courseenrollment__is_active=True,
        user__courseenrollment__course_id__exact=course_key
    ).filter(
        proforma_grade__lte=F('grade') + grade_complete_match_range,
        proforma_grade__gt=0
    ).exclude(user_id__in=exclude_users).count()

    course_metadata = CourseAggregatedMetaData.get_from_id(course_key)
    total_users_started = started['user__count']
    course_metadata.total_users_started = total_users_started
    course_metadata.total_users_completed = total_users_completed
    course_metadata.total_modules_completed = total_modules_completed
    course_metadata.save()


@task(name=u'lms.djangoapps.progress.tasks.cmc_post_save_task_handler')
def cmc_post_save_task_handler(course_id, content_id, user, cmc_created):
    """
    Performs tasks after course module completion
    """
    try:
        _update_course_user_progress(course_id, content_id, user, cmc_created)
    except Exception as ex:
        log.exception('An error occurred while updating course user progress: %s', ex.message)
        raise

    try:
        _update_course_metadata_aggregates(course_id)
    except Exception as ex:
        log.exception('An error occurred while updating course aggregates: %s', ex.message)
        raise
