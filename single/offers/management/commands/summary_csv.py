from django.core.management.base import BaseCommand
from offers import models
import csv


class Command(BaseCommand):
    help = 'Dump summary CSV'

    def handle(self, *args, **kwargs):
        from offers.logreg import logistic_regression
        import numpy
        from scipy.linalg import LinAlgError
        from scipy.linalg import inv
        import math

        writer = csv.writer(self.stdout)
        header_columns = ['Subject_number', 'Alpha Estimate', 'Beta Estimage', 'Indifference Point', 'Alpha SE', 'Beta SE', 'Happy with choice - Chose Other& ratio>ip', 'Happy with choice - Chose Other & ratio<=ip','Happy with choice - Chose Self & ratio>ip','Happy with choice - Chose Self & ratio<=ip']
        questions = models.Question.objects.all()
        q = questions.get(question_text="Please rate how happy you are with your choice. ")
        writer.writerow(header_columns)
        subjects = models.Subject.objects.all()
        for s in subjects:
            if s.finished():
                choices_np = s.choices_numpy()
                lr_np = s.log_ratios_numpy()
                try:
                    result = logistic_regression(lr_np, choices_np)
                    betas = result[0]
                    cov = inv(result[1])
                    std_err = cov.diagonal()**0.5 # Square root of diagonal!
                except LinAlgError:
                    result = 'Singular matrix'
                    betas = [5,.0001]
                    std_err = [0,0]

                try:
                    ip = (-1*betas[0])/betas[1]
                except ZeroDivisionError:
                    ip = 0

                if( ip > 3 ):
                    ip = 3
                elif( ip < -3 ):
                    ip = -3

                actual_minus_predicted = numpy.array([0, 0, 0, 0])
                actual = numpy.array([0, 0, 0, 0])
                predicted = numpy.array([0, 0, 0, 0])
                probe_count = numpy.array([0, 0, 0, 0])
                finished_probes = s.completed_probes()
                for probe in finished_probes:
                    probe_ratio = math.log(float(probe.choice.self_offer)/float(probe.choice.other_offer))
                    if( probe_ratio > 3 ):
                        probe_ratio = 3
                    elif( probe_ratio < -3 ):
                        probe_ratio = -3

                    probe_choice = probe.choice.chose_self
                    predicted_happiness = math.fabs(1.0/(1.0+numpy.exp(betas[0]+betas[1]*probe_ratio))-.5)*2.0

                    try:
                        resp = probe.response_set.get(question=q.id)
                        actual_minus_predicted[probe_choice*2+int(probe_ratio<=ip)] = actual_minus_predicted[probe_choice*2+int(probe_ratio<=ip)]+(resp.rating)-predicted_happiness*100;
                        actual[probe_choice*2+int(probe_ratio<=ip)] = actual[probe_choice*2+int(probe_ratio<=ip)]+(resp.rating)
                        predicted[probe_choice*2+int(probe_ratio<=ip)] = predicted[probe_choice*2+int(probe_ratio<=ip)]+(predicted_happiness*100)
                        probe_count[probe_choice*2+int(probe_ratio<=ip)] = probe_count[probe_choice*2+int(probe_ratio<=ip)]+1;
                    except:
                        pass

                actual_minus_predicted = (actual_minus_predicted/probe_count) - (actual_minus_predicted.sum()/probe_count.sum())

                actual = (actual/probe_count)
                predicted = (predicted/probe_count)
                # actual = (actual/probe_count) - (actual.sum()/probe_count.sum())

                # THERE SHOULD BE A MORE ELEGANT WAY TO WRITE THIS... I want to skip actual[i] where probe_count[i] = 0...
                # writer.writerow([s.session_and_subject, betas[0], betas[1], ip, std_err[0], std_err[1], actual_minus_predicted[0], actual_minus_predicted[1],actual_minus_predicted[2],actual_minus_predicted[3], probe_count[0], probe_count[1], probe_count[2], probe_count[3] ])
                writer.writerow([s.session_and_subject, betas[0], betas[1], ip, std_err[0], std_err[1], actual[0], actual[1],actual[2],actual[3], probe_count[0], probe_count[1], probe_count[2], probe_count[3] ])
                # writer.writerow([s.session_and_subject, betas[0], betas[1], ip, std_err[0], std_err[1], predicted[0], predicted[1],predicted[2],predicted[3], probe_count[0], probe_count[1], probe_count[2], probe_count[3] ])

                writer.writerow([s.session_and_subject, betas[0], betas[1], ip, std_err[0], std_err[1], actual[0], actual[1],actual[2],actual[3], predicted[0], predicted[1],predicted[2],predicted[3], actual_minus_predicted[0], actual_minus_predicted[1],actual_minus_predicted[2],actual_minus_predicted[3], probe_count[0], probe_count[1], probe_count[2], probe_count[3] ])
