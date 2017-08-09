"""
Serializers for the completion api
"""

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
    course_key = serializers.CharField()
    block_key = serializers.CharField()
    completion = _CompletionSerializer(source='*')


class SubsectionCourseCompletionSerializer(CourseCompletionSerializer):
    subsections = BlockCompletionSerializer(many=True)
