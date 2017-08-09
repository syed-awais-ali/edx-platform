"""
Test serialization of completion data.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import ddt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from mock import MagicMock, patch

from opaque_keys.edx.keys import CourseKey, UsageKey
from progress import models

from courseware.model_data import FieldDataCache
from courseware import module_render
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory
from ..serializers import CourseCompletionSerializer, SubsectionCourseCompletionSerializer
from ..models import CourseCompletionFacade


User = get_user_model()  # pylint: disable=invalid-name


class MockCourseCompletion(CourseCompletionFacade):
    """
    Provide CourseCompletion info without hitting the modulestore.
    """
    @property
    def possible(self):
        """
        Make up a number of possible blocks.  This prevents completable_blocks
        from being called, which prevents hitting the modulestore.
        """
        return 19

    @property
    def subsections(self):
        return [
            {'course_key': self.course_key, 'block_key': 'block1', 'earned': 6.0, 'possible': 7.0, 'percent': 86},
            {'course_key': self.course_key, 'block_key': 'block2', 'earned': 10.0, 'possible': 12.0, 'percent': 83},
        ]


@ddt.ddt
class CourseCompletionSerializerTestCase(TestCase):
    """
    Test that the CourseCompletionSerializer returns appropriate results.
    """

    @ddt.data(
        [CourseCompletionSerializer, {}],
        [
            SubsectionCourseCompletionSerializer,
            {
                'subsections': [
                    {
                        'course_key': 'course-v1:abc+def+ghi',
                        'block_key': 'block1',
                        'completion': {'earned': 6.0, 'possible': 7.0, 'percent': 86},
                    },
                    {
                        'course_key': 'course-v1:abc+def+ghi',
                        'block_key': 'block2',
                        'completion': {'earned': 10.0, 'possible': 12.0, 'percent': 83},
                    },
                ]
            }
        ]
    )
    @ddt.unpack
    def test_serialize_student_progress_object(self, serializer_cls, extra_body):
        test_user = User.objects.create(
            username='test_user',
            email='test_user@example.com'
        )
        progress = models.StudentProgress.objects.create(
            user=test_user,
            course_id=CourseKey.from_string('course-v1:abc+def+ghi'),
            completions=16,
        )
        completion = MockCourseCompletion(progress)
        serial = serializer_cls(completion)
        expected = {
            'course_key': 'course-v1:abc+def+ghi',
            'completion': {
                'earned': 16.0,
                'possible': 19.0,
                'percent': 84,
            },
        }
        expected.update(extra_body)
        self.assertEqual(
            serial.data,
            expected,
        )


@override_settings(STUDENT_GRADEBOOK=True)
class ToyCourseCompletionTestCase(SharedModuleStoreTestCase):
    """
    Test that the CourseCompletionFacade handles modulestore data appropriately,
    and that it interacts properly with the serializer.
    """

    @classmethod
    def setUpClass(cls):
        super(ToyCourseCompletionTestCase, cls).setUpClass()
        cls.course = ToyCourseFactory.create()

    def setUp(self):
        super(ToyCourseCompletionTestCase, self).setUp()
        self.test_user = User.objects.create(
            username='test_user',
            email='test_user@example.com'
        )

    def test_no_completions(self):
        progress = models.StudentProgress.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            completions=0,
        )
        completion = CourseCompletionFacade(progress)
        self.assertEqual(completion.earned, 0)
        self.assertEqual(completion.possible, 21)
        serial = CourseCompletionSerializer(completion)
        self.assertEqual(
            serial.data,
            {
                'course_key': 'edX/toy/2012_Fall',
                'completion': {
                    'earned': 0.0,
                    'possible': 21.0,
                    'percent': 0,
                }
            }
        )

    def test_with_completions(self):
        progress = models.StudentProgress.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            completions=3,
        )
        completion = CourseCompletionFacade(progress)
        self.assertEqual(completion.earned, 3)
        self.assertEqual(completion.possible, 21)
        self.assertEqual(len(completion.subsections), 1)
        serial = CourseCompletionSerializer(completion)
        self.assertEqual(
            serial.data,
            {
                'course_key': 'edX/toy/2012_Fall',
                'completion': {
                    'earned': 3.0,
                    'possible': 21.0,
                    'percent': 14,
                }
            }
        )

    def test_with_subsections(self):
        block_key = UsageKey.from_string("i4x://edX/toy/video/sample_video")
        block_key = block_key.map_into_course(self.course.id)
        module_completion = models.CourseModuleCompletion.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            content_id=block_key,
        )
        progress = models.StudentProgress.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            completions=1,
        )
        completion = CourseCompletionFacade(progress)
        serial = SubsectionCourseCompletionSerializer(completion)
        self.assertEqual(
            serial.data,
            {
                'course_key': 'edX/toy/2012_Fall',
                'completion': {
                    'earned': 1.0,
                    'possible': 21.0,
                    'percent': 5,
                },
                'subsections': [
                    {
                        'course_key': u'edX/toy/2012_Fall',
                        'block_key': u'i4x://edX/toy/sequential/vertical_sequential',
                        'completion': {'earned': 1.0, 'possible': 5.0, 'percent': 20},
                    }, 
                ]
            }
        )
