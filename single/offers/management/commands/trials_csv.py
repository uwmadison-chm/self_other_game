from django.core.management.base import BaseCommand
from offers import models
import csv


class Command(BaseCommand):
    help = 'Dump trials as CSV'

    def handle(self, *args, **kwargs):
        writer = csv.writer(self.stdout)
        header_columns = [
            'Choice ID', 'Subject number', 'Self offer', 'Other offer',
            'Chose self', 'Ratio', 'Onset msec', 'Response msec',
            'Alpha Estimate', 'Beta Estimate'
        ]
        writer.writerow(header_columns)
        trials = models.Choice.objects.filter(chose_self__isnull=False)
        for trial in trials:
            # probing = trial.probings_set.all()
            self_int = 0
            if trial.chose_self:
                self_int = 1
            displayed, responded = ['', '']
            try:
                displayed, responded = trial.timings.split(":")
                subj = trial.subject
                writer.writerow([
                    trial.pk, subj.session_and_subject, trial.self_offer,
                    trial.other_offer, self_int, trial.ratio(), displayed,
                    responded, subj.alpha_estimate, subj.beta_estimate
                ])
            except:
                self.stderr.write("OH NO\n")
