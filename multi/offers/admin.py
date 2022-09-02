from models import Session, Subject, Choice, Question, Pairing, ScheduledPairing
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect


class SubjectInline(admin.TabularInline):
    model = Subject
    
    fieldsets = (
        (None, {'fields': ('computed_amount', 'paid_amount')}),
    )

    extra = 0
    template = "admin/offers/subject_inline_form.html"
    
class ButtonableModelAdmin(admin.ModelAdmin):
    buttons = []
    
    def change_view(self, request, object_id, extra_context = {}):
        extra_context['buttons'] = self.buttons
        return super(ButtonableModelAdmin, self).change_view(
            request, object_id, extra_context)
    
    def __call__(self, request, url):
        if url is not None:
            import re
            res=re.match('(.*/)?(?P<id>\d+)/(?P<command>.*)', url)
            if res and res.group('command') in [b.func_name for b in self.buttons]:
                obj = self.model._default_manager.get(pk=res.group('id'))
                getattr(self, res.group('command'))(obj)
                return HttpResponseRedirect(request.META['HTTP_REFERER'])
        
        return super(ButtonableModelAdmin, self).__call__(request, url)

class SessionAdmin(ButtonableModelAdmin):
    inlines = [ SubjectInline, ]
    save_on_top = True
     
    def compute_payouts(self, obj):
        obj.compute_payouts()
    
    compute_payouts.short_description = "Compute payouts"
    
    buttons = [compute_payouts]

class SubjectAdmin(admin.ModelAdmin):
    search_fields = ['subject_number']
    list_filter = ['session']
    list_display = ['session_and_subject', 'finished', 'diagnostic_link']    
    

    
admin.site.register(Pairing)
admin.site.register(ScheduledPairing)
admin.site.register(Session, SessionAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Choice)
admin.site.register(Question)
