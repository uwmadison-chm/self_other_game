from django import forms
from django.forms.formsets import formset_factory

from models import Subject, Session

class SubjectLocatorField(forms.CharField):
    """ 
    This should be of the form session_number-subject_number. Examples:
    001-103829, 1020-181024
    
    """
    def clean(self, value):
        try:
            sess_num, subj_num = value.split("-")
            sess = Session.objects.get(session_number=sess_num)
            subj = sess.subject_set.get(subject_number=subj_num)
        except:
            raise forms.ValidationError("Subject not found")
        
        return value

class LoginForm(forms.Form):
    subject_number = SubjectLocatorField(max_length=30)
