"""
Model code for completion API, including django models and facade classes
wrapping progress extension models.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from opaque_keys.edx.keys import UsageKey

from lms.djangoapps.course_blocks.api import get_course_blocks
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from progress.models import CourseModuleCompletion


IGNORE_CATEGORIES = {
    # Structural types
    'course',
    'chapter',
    'sequential',
    'vertical',

    # Non-completable types
    'discussion-course',
    'group-project',
    'discussion-forum',
    'eoc-journal',

    # GP v2 categories
    'gp-v2-project',
    'gp-v2-activity',
    'gp-v2-stage-basic',
    'gp-v2-stage-completion',
    'gp-v2-stage-submission',
    'gp-v2-stage-team-evaluation',
    'gp-v2-stage-peer-review',
    'gp-v2-stage-evaluation-display',
    'gp-v2-stage-grade-display',
    'gp-v2-resource',
    'gp-v2-video-resource',
    'gp-v2-submission',
    'gp-v2-peer-selector',
    'gp-v2-group-selector',
    'gp-v2-review-question',
    'gp-v2-peer-assessment',
    'gp-v2-group-assessment',
    'gp-v2-static-submissions',
    'gp-v2-static-grade-rubric',
    'gp-v2-project-team',
    'gp-v2-navigator',
    'gp-v2-navigator-navigation',
    'gp-v2-navigator-resources',
    'gp-v2-navigator-submissions',
    'gp-v2-navigator-ask-ta',
    'gp-v2-navigator-private-discussion',
}


class CourseCompletionFacade(object):
    """
    Facade wrapping progress.models.StudentProgress model.
    """

    def __init__(self, inner):
        self._blocks = None
        self._collected = None
        self._completable_blocks = None
        self._inner = inner

    @property
    def collected(self):
        """
        Return the collected block structure for this course
        """
        if self._collected is None:
            self._collected = get_course_in_cache(self.course_key)
        return self._collected

    @property
    def blocks(self):
        """
        Return all blocks in the course.
        """
        if self._blocks is None:
            course_location = CourseOverview.load_from_module_store(self.course_key).location
            self._blocks = get_course_blocks(
                self.user,
                course_location,
                collected_block_structure=self.collected,
            )
        return self._blocks

    @property
    def completable_blocks(self):
        """
        Return the set of blocks that can be completed that are visible to
        self.user.

        This method encapsulates the facade's access to the modulestore, making
        it a useful candidate for mocking.
        """
        if self._completable_blocks is None:
            self._completable_blocks = {
                block for block in self.blocks
                if self.blocks.get_xblock_field(block, 'category') not in IGNORE_CATEGORIES
            }
        return self._completable_blocks

    @property
    def user(self):
        """
        Return the StudentProgress user
        """
        return self._inner.user

    @property
    def course_key(self):
        """
        Return the StudentProgress course_key
        """
        return self._inner.course_id

    @property
    def earned(self):
        """
        Return the number of completions earned by the user.
        """

        return self._inner.completions

    @property
    def possible(self):
        """
        Return the maximum number of completions the user could earn in the
        course.
        """

        return float(len(self.completable_blocks))

    @property
    def percent(self):
        """
        Return the percent of the course completed by the user.

        Percent is returned as an integer between 0 and 100.
        """
        return int(round(100 * self.earned / self.possible))

    def get_blocks_by_category(self, category):
        """
        Return all blocks of the specified category
        """
        for block in self.blocks:
            if self.blocks.get_xblock_field(block, 'category') == category:
                yield block

    @property
    def subsections(self):
        """
        Return the BlockCompletion for all subsections.
        """
        subsections = []
        for block in self.get_blocks_by_category('sequential'):
            subsections.append(BlockCompletion(self.user, block, self))
        return subsections


class BlockCompletion(object):
    """
    Class to represent completed blocks within a given block of the course.
    """

    def __init__(self, user, block_key, course_completion):
        self.user = user
        self.block_key = block_key
        self.course_key = block_key.course_key
        self.course_completion = course_completion
        self._blocks = None
        self._completable_blocks = None

    @property
    def blocks(self):
        """
        Return all blocks within the requested block.
        """
        if self._blocks is None:

            self._blocks = get_course_blocks(
                self.user,
                self.block_key,
                collected_block_structure=self.course_completion.collected,
            )
        return self._blocks

    @property
    def completable_blocks(self):
        """
        Return the set of keys of all blocks within self.block that can be
        completed by self.user.

        This method encapsulates the class' access to the modulestore, making
        it a useful candidate for mocking.
        """
        if self._completable_blocks is None:
            self._completable_blocks = {
                block.map_into_course(self.course_key) for block in self.blocks
                if self.blocks.get_xblock_field(block, 'category') not in IGNORE_CATEGORIES
            }
        return self._completable_blocks

    @property
    def completed_blocks(self):
        """
        Return the set of keys of all blocks within self.block that have been
        completed by self.user.
        """
        modules = CourseModuleCompletion.objects.filter(
            user=self.user,
            course_id=self.course_key
        )
        module_keys = {UsageKey.from_string(mod.content_id).map_into_course(self.course_key) for mod in modules}
        print(module_keys)
        print(self.completable_blocks)
        print(module_keys & self.completable_blocks)
        return module_keys & self.completable_blocks

    @property
    def earned(self):
        """
        The number of earned completions within self.block.
        """
        return float(len(self.completed_blocks))

    @property
    def possible(self):
        """
        The number of possible completions within self.block.
        """
        return float(len(self.completable_blocks))

    @property
    def percent(self):
        """
        Return the percent of the course completed by the user.

        Percent is returned as an integer between 0 and 100.
        """
        return int(round(100 * self.earned / self.possible))
