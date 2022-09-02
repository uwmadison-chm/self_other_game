from django import forms
from django.forms.formsets import formset_factory

import models
import logging as logger

class SubjectLocatorField(forms.CharField):
    """ 
    This should be of the form session_number-subject_number. Examples:
    001-103829, 1020-181024
    
    """
    def clean(self, value):
        sess_num, subj_num = value.split("-")
        logger.debug((sess_num, subj_num))
        try:
            sess = models.Session.objects.get(session_number=sess_num)
            subj = sess.subject_set.get(subject_number=subj_num)
        except models.Session.DoesNotExist:
            raise forms.ValidationError("Session not found")
        except models.Subject.DoesNotExist:
            raise forms.ValidationError("Subject not found")
        
        return value

class LoginForm(forms.Form):
    subject_number = SubjectLocatorField(max_length=30)
