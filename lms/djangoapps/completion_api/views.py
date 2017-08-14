"""
API views to read completion information.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey
from progress.models import StudentProgress
from rest_framework.exceptions import NotAuthenticated, NotFound, ParseError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.lib.api import authentication, paginators

from .models import CourseCompletionFacade
from .serializers import CourseCompletionSerializer, SubsectionCourseCompletionSerializer

User = get_user_model()  # pylint: disable=invalid-name


class CompletionViewMixin(object):
    """
    Common functionality for completion views.
    """

    _allowed_extra_fields = {'subsections'}

    authentication_classes = (
        authentication.OAuth2AuthenticationAllowInactiveUser,
        authentication.SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (IsAuthenticated,)

    def get_user(self):
        """
        Return the effective user.

        Usually the requesting user, but a staff user can override this.
        """
        # TODO: Allow staff user to specify any learner.
        requested_username = self.request.GET.get('user')
        if requested_username is None:
            user = self.request.user
        else:
            if self.request.user.is_staff:
                try:
                    user = User.objects.get(username=requested_username)
                except User.DoesNotExist:
                    raise PermissionDenied()
            else:
                if self.request.user.username.lower() == requested_username.lower():
                    user = self.request.user
                else:
                    raise NotFound()
        if not user.is_authenticated():
            raise NotAuthenticated()
        return user

    def get_progress_queryset(self):
        """
        Build a base queryset of relevant StudentProgress objects.
        """
        objs = StudentProgress.objects.filter(user=self.get_user())
        return objs

    def get_extra_fields(self):
        """
        Parse and return value for extra_fields parameter.
        """
        fields = set(field for field in self.request.GET.get('extra_fields', '').split(',') if field)
        diff = fields - self._allowed_extra_fields
        if diff:
            msg = 'Invalid extra_fields value: {}.  Allowed values: {}'
            raise ParseError(msg.format(fields, self._allowed_extra_fields))
        return fields

    def get_serializer(self):
        """
        Return the appropriate serializer.
        """
        if 'subsections' in self.get_extra_fields():
            serializer = SubsectionCourseCompletionSerializer
        else:
            serializer = CourseCompletionSerializer
        return serializer


class CompletionListView(APIView, CompletionViewMixin):
    """
    API view to render lists of serialized CourseCompletions.

    This is a transitional implementation that uses the
    edx-solutions/progress-edx-platform-extensions models as a backing store.
    """

    pagination_class = paginators.NamespacedPageNumberPagination

    def get(self, request):
        """
        Handler for GET requests.
        """
        self.paginator = self.pagination_class()
        paginated = self.paginator.paginate_queryset(self.get_progress_queryset(), self.request, view=self)
        completions = [CourseCompletionFacade(progress) for progress in paginated]
        return self.paginator.get_paginated_response(self.get_serializer()(completions, many=True).data)


class CompletionDetailView(APIView, CompletionViewMixin):
    """
    API view to render serialized CourseCompletions.

    This is a transitional implementation that uses the
    edx-solutions/progress-edx-platform-extensions models as a backing store.
    """

    def get(self, request, course_key):
        """
        Handler for GET requests.
        """
        course_key = CourseKey.from_string(course_key)
        print("looking for key:", (course_key, type(course_key)))
        progress = self.get_progress_queryset().get(course_id=course_key)
        completion = CourseCompletionFacade(progress)
        return Response(self.get_serializer()(completion).data)
