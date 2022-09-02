# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Session'
        db.create_table('offers_session', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('scm_revision', self.gf('django.db.models.fields.CharField')(default='.', max_length=255)),
            ('total_trials', self.gf('django.db.models.fields.IntegerField')(default=200)),
            ('total_probings', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('distribution_sigma', self.gf('django.db.models.fields.FloatField')(default=0.25)),
            ('minimum_offer', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('maximum_offer', self.gf('django.db.models.fields.IntegerField')(default=1000)),
        ))
        db.send_create_signal('offers', ['Session'])

        # Adding model 'Subject'
        db.create_table('offers_subject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('scm_revision', self.gf('django.db.models.fields.CharField')(default='.', max_length=255)),
            ('subject_number', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('alpha_estimate', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('beta_estimate', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['offers.Session'])),
            ('computed_amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('paid_amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('offers', ['Subject'])

        # Adding unique constraint on 'Subject', fields ['session', 'subject_number']
        db.create_unique('offers_subject', ['session_id', 'subject_number'])

        # Adding model 'Choice'
        db.create_table('offers_choice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('scm_revision', self.gf('django.db.models.fields.CharField')(default='.', max_length=255)),
            ('subject', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['offers.Subject'])),
            ('self_offer', self.gf('django.db.models.fields.IntegerField')()),
            ('other_offer', self.gf('django.db.models.fields.IntegerField')()),
            ('chose_self', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('timings', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('offers', ['Choice'])

        # Adding model 'Question'
        db.create_table('offers_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('scm_revision', self.gf('django.db.models.fields.CharField')(default='.', max_length=255)),
            ('question_text', self.gf('django.db.models.fields.TextField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('offers', ['Question'])

        # Adding model 'Probing'
        db.create_table('offers_probing', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('scm_revision', self.gf('django.db.models.fields.CharField')(default='.', max_length=255)),
            ('subject', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['offers.Subject'])),
            ('choice', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['offers.Choice'])),
            ('paired_with', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['offers.Probing'], unique=True, null=True, blank=True)),
            ('timing_data_json', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('offers', ['Probing'])

        # Adding model 'Response'
        db.create_table('offers_response', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('scm_revision', self.gf('django.db.models.fields.CharField')(default='.', max_length=255)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['offers.Question'])),
            ('probing', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['offers.Probing'])),
            ('rating', self.gf('django.db.models.fields.FloatField')(default=50)),
            ('question_text', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('offers', ['Response'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Subject', fields ['session', 'subject_number']
        db.delete_unique('offers_subject', ['session_id', 'subject_number'])

        # Deleting model 'Session'
        db.delete_table('offers_session')

        # Deleting model 'Subject'
        db.delete_table('offers_subject')

        # Deleting model 'Choice'
        db.delete_table('offers_choice')

        # Deleting model 'Question'
        db.delete_table('offers_question')

        # Deleting model 'Probing'
        db.delete_table('offers_probing')

        # Deleting model 'Response'
        db.delete_table('offers_response')


    models = {
        'offers.choice': {
            'Meta': {'ordering': "['subject', 'id']", 'object_name': 'Choice'},
            'chose_self': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'other_offer': ('django.db.models.fields.IntegerField', [], {}),
            'scm_revision': ('django.db.models.fields.CharField', [], {'default': "'.'", 'max_length': '255'}),
            'self_offer': ('django.db.models.fields.IntegerField', [], {}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.Subject']"}),
            'timings': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'offers.probing': {
            'Meta': {'ordering': "['subject', 'id']", 'object_name': 'Probing'},
            'choice': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.Choice']"}),
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'paired_with': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.Probing']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'scm_revision': ('django.db.models.fields.CharField', [], {'default': "'.'", 'max_length': '255'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.Subject']"}),
            'timing_data_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'offers.question': {
            'Meta': {'ordering': "['-active', 'order', 'id']", 'object_name': 'Question'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'question_text': ('django.db.models.fields.TextField', [], {}),
            'scm_revision': ('django.db.models.fields.CharField', [], {'default': "'.'", 'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'offers.response': {
            'Meta': {'ordering': "['probing', 'question', 'id']", 'object_name': 'Response'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'probing': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.Probing']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.Question']"}),
            'question_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'rating': ('django.db.models.fields.FloatField', [], {'default': '50'}),
            'scm_revision': ('django.db.models.fields.CharField', [], {'default': "'.'", 'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'offers.session': {
            'Meta': {'object_name': 'Session'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'distribution_sigma': ('django.db.models.fields.FloatField', [], {'default': '0.25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maximum_offer': ('django.db.models.fields.IntegerField', [], {'default': '1000'}),
            'minimum_offer': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'scm_revision': ('django.db.models.fields.CharField', [], {'default': "'.'", 'max_length': '255'}),
            'total_probings': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'total_trials': ('django.db.models.fields.IntegerField', [], {'default': '200'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'offers.subject': {
            'Meta': {'unique_together': "(('session', 'subject_number'),)", 'object_name': 'Subject'},
            'alpha_estimate': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'beta_estimate': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'computed_amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'paid_amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'scm_revision': ('django.db.models.fields.CharField', [], {'default': "'.'", 'max_length': '255'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.Session']"}),
            'subject_number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['offers']
