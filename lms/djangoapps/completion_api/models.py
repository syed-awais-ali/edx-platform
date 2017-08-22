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


AGGREGATABLE_BLOCK_CATEGORIES = {
    'chapter',
    'sequential',
    'vertical',
}

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


class CompletionsByCategory(property):
    """
    A reusable read-only property that returns the BlockCompletions for a given
    block category.

    Block categories must be chosen from within AGGREGATABLE_BLOCK_CATEGORIES.

    This property requires the attribute self._completions_by_category to be
    available on objects that implement it.
    """
    # pylint: disable=protected-access

    def __init__(self, category):  # pylint: disable=super-init-not-called
        if category not in AGGREGATABLE_BLOCK_CATEGORIES:
            raise InvalidBlockCategory
        self.category = category
        self.fset = None
        self.fdel = None

    def __doc__(self):
        return u'Completions of blocks with the category {:r}'.format(self.category)

    def fget(self, obj):
        """
        Calculate completions at category level, caching the result on
        the containing object.
        """
        if obj._completions_by_category is None:
            obj._completions_by_category = {}
        if self.category not in obj._completions_by_category:
            completions = []
            for block_key in obj.iter_block_keys_in_category(self.category):
                completions.append(BlockCompletion(obj.user, block_key, self))
            obj._completions_by_category[self.category] = completions
        return obj._completions_by_category[self.category]


class CompletionDataMixin(object):
    """
    Common calculations for completion values of courses or blocks within courses.

    Classes using this mixin must implement:

        * self.earned (float)
        * self.completable_blocks (Collection<UsageKey>)
    """

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
        if self.possible == 0:
            percent = 100
        else:
            percent = int(round(100 * self.earned / self.possible))
        return percent


class CourseCompletionFacade(CompletionDataMixin, object):
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
        Return an
        `openedx.core.lib.block_structure.block_structure.BlockStructureBlockData`
        collection which behaves as dict that maps
        `opaque_keys.edx.locator.BlockUsageLocator`s to
        `openedx.core.lib.block_structure.block_structure.BlockData` objects
        for all blocks in the course.
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
        Return a set of UsageKeys for all blocks that can be completed that are
        visible to self.user.

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

    def iter_block_keys_in_category(self, category):
        """
        Yields the UsageKey for all blocks of the specified category.
        """
        for block in self.blocks:
            if self.blocks.get_xblock_field(block, 'category') == category:
                yield block

    chapters = CompletionsByCategory('chapter')
    sequentials = CompletionsByCategory('sequential')
    verticals = CompletionsByCategory('vertical')


class BlockCompletion(CompletionDataMixin, object):
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
        Return an `openedx.core.lib.block_structure.block_structure.BlockStructureBlockData`
        object which behaves as dict that maps `opaque_keys.edx.locator.BlockUsageLocator`s
        to `openedx.core.lib.block_structure.block_structure.BlockData` objects
        for all blocks in the sub-tree (or DAG) under self.block_key.
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
        Return the set of UsageKeys of all blocks within self.block that can be
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
        Return the set of UsageKeys of all blocks within self.block that have been
        completed by self.user.
        """
        modules = CourseModuleCompletion.objects.filter(
            user=self.user,
            course_id=self.course_key
        )
        module_keys = {UsageKey.from_string(mod.content_id).map_into_course(self.course_key) for mod in modules}
        return module_keys & self.completable_blocks

    @property
    def earned(self):
        """
        The number of earned completions within self.block.
        """
        return float(len(self.completed_blocks))


class InvalidBlockCategory(TypeError):
    """
    An exception raised when trying to access an invalid block category
    """
    pass
