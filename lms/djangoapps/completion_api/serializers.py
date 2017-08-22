"""
Serializers for the completion api
"""

#pylint: disable=abstract-method

from __future__ import absolute_import, division, print_function, unicode_literals

from rest_framework import serializers


class _CompletionSerializer(serializers.Serializer):
    """
    Inner serializer for actual completion data.
    """
    earned = serializers.FloatField()
    possible = serializers.FloatField()
    percent = serializers.IntegerField()


class CourseCompletionSerializer(serializers.Serializer):
    """
    Serialize completions at the course level.
    """
    course_key = serializers.CharField()
    completion = _CompletionSerializer(source='*')


class BlockCompletionSerializer(serializers.Serializer):
    """
    A serializer that represents nested aggregations of sub-graphs
    of xblocks.
    """
    course_key = serializers.CharField()
    block_key = serializers.CharField()
    completion = _CompletionSerializer(source='*')


def course_completion_serializer_factory(extra_fields):
    """
    Create a CourseCompletionSerializer that nests appropriate
    BlockCompletionSerializers for the specified extra_fields.
    """
    dunder_dict = {
        field: BlockCompletionSerializer(many=True) for field in extra_fields
    }
    return type(
        'CourseCompletionSerializerWithAggregates',
        [CourseCompletionSerializer],
        dunder_dict,
    )
