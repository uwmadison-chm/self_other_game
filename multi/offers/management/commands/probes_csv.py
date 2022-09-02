from django.core.management.base import BaseCommand
from offers import models
import csv


class Command(BaseCommand):
    help = 'Dump probes as CSV'

    def handle(self, *args, **kwargs):
        writer = csv.writer(self.stdout)
        # First, find all of the extant questions
        questions = models.Question.objects.all()

        header_columns = [
            'Subject number', 'Self offer', 'Other offer', 'Chose self', 'Ratio', 'Pairing'
        ]

        for q in questions:
            header_columns.append("Q%s rating" % q.id)
            header_columns.append("Q%s text" % q.id)
        header_columns.append("Timings JSON")
        writer.writerow(header_columns)

        probings = models.Probing.objects.filter(completed=True)
        for p in probings:
            csi = 0
            if p.choice.chose_self:
                csi = 1
            subj = p.subject
            data = [
                subj.session_and_subject, p.choice.self_offer,
                p.choice.other_offer, csi, p.choice.ratio(),
                p.pairing.description
            ]

            for q in questions:
                try:
                    # Is the ORM optimizer smart enough not to n+1 this?
                    resp = p.response_set.get(question=q.id)
                    data.append(resp.rating)
                    data.append(resp.question_text)
                except:
                    # No matching question.
                    data.append('')
                    data.append('')

            data.append(p.timing_data_json)
            writer.writerow(data)