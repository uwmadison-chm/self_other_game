from django.core.management.base import BaseCommand
from offers import models
import csv
from offers.logreg import logistic_regression
from scipy.linalg import LinAlgError
from scipy.linalg import inv


class Command(BaseCommand):
    help = 'Dump summary CSV'

    def handle(self, *args, **kwargs):
        writer = csv.writer(self.stdout)

        header_columns = [
            'Subject number', 'Trial number', 'Self offer', 'Other offer',
            'Chose self', 'Alpha Estimate', 'Beta Estimate',
            'Stderr(Alpha)', 'Stderr(Beta)'
        ]
        writer.writerow(header_columns)
        for subject in models.Subject.objects.all():
            choices_np = subject.choices_numpy()
            lr_np = subject.log_ratios_numpy()
            offers_np = subject.offers_numpy().astype(int)

            for i in range(len(choices_np)):
                #logger.debug("Working on subject %s trial %s" %
                #            (subject.session_and_subject, i+1))
                try:
                    result = logistic_regression(lr_np[:i+1], choices_np[:i+1])
                    betas = result[0]
                    cov = inv(result[1])
                    std_err = cov.diagonal()**0.5 # Square root of diagonal!
                except LinAlgError:
                    result = 'Singular matrix'
                    betas = ['nan','nan']
                    std_err = ['nan','nan']

                row = [
                    subject.session_and_subject, i+1, offers_np[i][0], offers_np[i][1],
                    int(choices_np[i]), betas[0], betas[1],
                    std_err[0], std_err[1]
                ]
                writer.writerow(row)
