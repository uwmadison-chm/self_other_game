from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import *
from django.utils import simplejson

import models

def show(request, session_num, format):
    format = format or "html"
    session = get_object_or_404(models.Session, pk=int(session_num))
    subjects = session.subject_set.all()
    if format == "js":
        return HttpResponse(
            simplejson.dumps(
                {
                    "session_number" : session.session_number(),
                    "session_date" : str(session.session_date),
                    "subjects":[str(s.subject_number) for s in subjects]
                
                }
            ),
            content_type="text/javascript"
        )
    else:
        return render_to_response("subject_list.djhtml", {
            'session' : session,
            'subjects' : subjects
        })