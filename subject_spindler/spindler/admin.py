from django.contrib import admin
from models import Session, Subject

class SubjectInline(admin.StackedInline):
    model = Subject
    
    fieldsets = (
        (None, {'fields': ()}),
    )

    extra = 0

class SessionAdmin(admin.ModelAdmin):
    inlines = [ SubjectInline, ]
    

admin.site.register(Session, SessionAdmin)
admin.site.register(Subject)