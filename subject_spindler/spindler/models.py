from django.db import models
from django.conf import settings

# A base that everything should inherit from -- includes columns for
# timestamps and SCM data.
class StampedTrackedModel(models.Model):
    # Timestamp columns
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # And the scm_revision
    scm_revision = models.CharField(
        "SCM Revision", max_length=255, default=settings.REPOSITORY_URL, editable=False)

    class Meta:
        abstract = True


class Session(StampedTrackedModel):
    """A session in the system -- basically, a container for subjects."""
    
    subject_count = models.IntegerField()
    session_date = models.DateField()
    
    def __unicode__(self):
        """ Looks like 030: 2010-10-23 """
        return "%s: %s" % (self.session_number(), self.session_date)
    
    def session_number(self):
        return "%03u" % (self.pk)
    
    def save(self, *args, **kwargs):
        
        super(Session, self).save(*args, **kwargs)
        new_subject_count = self.subject_count - self.subject_set.count()
        for x in range(0, new_subject_count):
            self.subject_set.create()
        
    
class Subject(StampedTrackedModel):
    session = models.ForeignKey("Session")
    
    subject_number = models.CharField(max_length = 10, blank = True)
    
    class Meta:
        unique_together = (('session', 'subject_number'))
    
    def save(self, *args, **kwargs):
        from random import randint
        
        if self.pk is None:
            self.subject_number = ''.join(
                [str(randint(0,9)) for x in range(0,6)]
            )
        
        super(Subject, self).save(*args, **kwargs)
    
    def __unicode__(self):
        """ These look like 030-471948 """
        return "%03u-%s" % (self.session.pk, self.subject_number)