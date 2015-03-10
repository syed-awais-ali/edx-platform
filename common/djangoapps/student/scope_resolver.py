"""
A User Scope Resolver that can be used by edx-notifications
"""

import logging

from edx_notifications.scopes import NotificationUserScopeResolver
from student.models import CourseEnrollment

log = logging.getLogger(__name__)


class CourseEnrollmentsScopeResolver(NotificationUserScopeResolver):
    """
    Implementation of the NotificationUserScopeResolver abstract
    interface defined in edx-notifications.

    An instance of this class will be registered to handle
    scope_name = 'course_enrollments' during system startup.

    We will be passed in a course_id in the context
    and we must return a Django ORM resultset or None if
    we cannot match.
    """

    def resolve(self, scope_name, scope_context, instance_context):
        """
        The entry point to resolve a scope_name with a given scope_context
        """

        if scope_name != 'course_enrollments':
            # we can't resolve any other scopes
            return None

        if 'course_id' not in scope_context:
            # did not receive expected parameters
            return None

        return CourseEnrollment.objects.values_list('user_id', flat=True).filter(
            is_active=1,
            course_id=scope_context['course_id']
        )
