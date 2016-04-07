# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CourseAggregatedMetaData.total_users_started'
        db.add_column('course_metadata_courseaggregatedmetadata', 'total_users_started',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CourseAggregatedMetaData.total_users_completed'
        db.add_column('course_metadata_courseaggregatedmetadata', 'total_users_completed',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CourseAggregatedMetaData.total_modules_completed'
        db.add_column('course_metadata_courseaggregatedmetadata', 'total_modules_completed',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'CourseAggregatedMetaData.total_users_started'
        db.delete_column('course_metadata_courseaggregatedmetadata', 'total_users_started')

        # Deleting field 'CourseAggregatedMetaData.total_users_completed'
        db.delete_column('course_metadata_courseaggregatedmetadata', 'total_users_completed')

        # Deleting field 'CourseAggregatedMetaData.total_modules_completed'
        db.delete_column('course_metadata_courseaggregatedmetadata', 'total_modules_completed')


    models = {
        'course_metadata.courseaggregatedmetadata': {
            'Meta': {'object_name': 'CourseAggregatedMetaData'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'primary_key': 'True', 'db_index': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'total_assessments': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_modules': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_modules_completed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_users_completed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_users_started': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['course_metadata']