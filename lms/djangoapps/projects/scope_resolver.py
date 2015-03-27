"""
A User Scope Resolver that can be used by edx-notifications
"""

import logging

from edx_notifications.scopes import NotificationUserScopeResolver
from projects.models import Project

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

        if 'content_id' not in scope_context:
            # did not receive expected parameters
            return None

        content_id = scope_context['content_id']

        return Project.get_user_ids_in_project_by_content_id(content_id)
