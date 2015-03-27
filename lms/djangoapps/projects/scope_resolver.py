"""
A User Scope Resolver that can be used by edx-notifications
"""

import logging

from edx_notifications.scopes import NotificationUserScopeResolver
from projects.models import Project

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey

log = logging.getLogger(__name__)


class GroupProjectParticipantsScopeResolver(NotificationUserScopeResolver):
    """
    Implementation of the NotificationUserScopeResolver abstract
    interface defined in edx-notifications.

    An instance of this class will be registered to handle
    scope_name = 'group_project_participants' during system startup.

    We will be passed in a content_id in the context
    and we must return a Django ORM resultset or None if
    we cannot match.
    """

    def resolve(self, scope_name, scope_context, instance_context):
        """
        The entry point to resolve a scope_name with a given scope_context
        """

        if scope_name != 'group_project_participants':
            # we can't resolve any other scopes
            return None

        content_id = scope_context.get('content_id')
        course_id = scope_context.get('course_id')

        if not content_id or not course_id:
            return None

        return Project.get_user_ids_in_project_by_content_id(course_id, content_id)
