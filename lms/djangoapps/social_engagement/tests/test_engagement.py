"""
Tests for the social_engagment subsystem

paver test_system -s lms --test_id=lms/djangoapps/social_engagements/tests/test_engagement.py
"""

from django.conf import settings
from django.db import IntegrityError

from mock import MagicMock, patch
from datetime import datetime
from django.utils.timezone import UTC

from django.test import TestCase
from django.test.utils import override_settings


from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.factories import CourseFactory

from social_engagement.models import StudentSocialEngagementScore, StudentSocialEngagementScoreHistory

from social_engagement.engagement import update_user_engagement_scores
from social_engagement.engagement import update_course_engagement_scores
from social_engagement.engagement import update_all_courses_engagement_scores

from edx_notifications.startup import initialize as initialize_notifications
from edx_notifications.lib.consumer import get_notifications_count_for_user


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@patch.dict(settings.FEATURES, {'ENABLE_NOTIFICATIONS': True})
class StudentEngagementTests(TestCase):
    """ Test suite for CourseModuleCompletion """

    def setUp(self):
        self.user = UserFactory()
        self.user2 = UserFactory()

        self._create_course()

        initialize_notifications()

    def _create_course(self, start=None, end=None):
        self.course = CourseFactory.create(
            start=start,
            end=end
        )

        CourseEnrollment.enroll(self.user, self.course.id)
        CourseEnrollment.enroll(self.user2, self.course.id)

    def test_no_engagment_records(self):
        """
        Verify that we get None back
        """

        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user.id))
        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user2.id))

        # no entries, means a rank of 0!
        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['score'],
            0
        )

        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['position'],
            0
        )

        self.assertFalse(
            StudentSocialEngagementScore.generate_leaderboard(self.course.id)
        )

    def test_save_first_engagement_score(self):
        """
        Basic write operation
        """

        self.assertEqual(get_notifications_count_for_user(self.user.id), 0)

        StudentSocialEngagementScore.save_user_engagment_score(self.course.id, self.user.id, 10)

        # read it back
        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['score'],
            10
        )

        # confirm there is an entry in the History table
        self.assertEqual(
            StudentSocialEngagementScoreHistory.objects.filter(
                course_id=self.course.id,
                user__id=self.user.id
            ).count(),
            1
        )

        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['position'],
            1
        )

        # look at the leaderboard
        leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course.id)
        self.assertIsNotNone(leaderboard)
        self.assertEqual(len(leaderboard), 1)

        self.assertEqual(leaderboard[0]['user__id'], self.user.id)
        self.assertEqual(leaderboard[0]['score'], 10)

        # confirm there is a notification was generated
        self.assertEqual(get_notifications_count_for_user(self.user.id), 1)

    def test_update_engagement_score(self):
        """
        Basic update operation
        """

        self.assertEqual(get_notifications_count_for_user(self.user.id), 0)

        StudentSocialEngagementScore.save_user_engagment_score(self.course.id, self.user.id, 10)

        # then update
        StudentSocialEngagementScore.save_user_engagment_score(self.course.id, self.user.id, 20)

        # read it back
        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['score'],
            20
        )

        # confirm there are two entries in the History table
        self.assertEqual(
            StudentSocialEngagementScoreHistory.objects.filter(
                course_id=self.course.id,
                user__id=self.user.id
            ).count(),
            2
        )

        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['position'],
            1
        )

        # look at the leaderboard
        leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course.id)
        self.assertIsNotNone(leaderboard)
        self.assertEqual(len(leaderboard), 1)

        self.assertEqual(leaderboard[0]['user__id'], self.user.id)
        self.assertEqual(leaderboard[0]['score'], 20)

        # confirm there is a just a single notification was generated
        self.assertEqual(get_notifications_count_for_user(self.user.id), 1)

    def test_score_integrity(self):
        """
        Make sure we can't have duplicate course_id/user_id pais
        """

        StudentSocialEngagementScore.save_user_engagment_score(self.course.id, self.user.id, 10)

        again = StudentSocialEngagementScore(course_id=self.course.id, user_id=self.user.id, score=20)

        with self.assertRaises(IntegrityError):
            again.save()
