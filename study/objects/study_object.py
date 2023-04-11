from study.models import Study
from study.exceptions import StudyDoesNotExistExceptions
from runner.models import Run, RunStatus


class StudyObject(object):

    def __init__(self, study_id, requests, samples, db_object):
        self.study_id = study_id
        self.requests = requests
        self.samples = samples
        self.db_object = db_object

    @classmethod
    def from_db(cls, study_id):
        try:
            study = Study.objects.get(study_id=study_id)
        except Study.DoesNotExist:
            raise StudyDoesNotExistExceptions
        return cls(
            study_id=study_id,
            requests=list(study.requests.all()),
            samples=list(study.samples.all()),
            db_object=study
        )

    @staticmethod
    def get_by_request(request_id):
        studies = Study.objects.filter(requests__request_id__contains=request_id).all()
        return [StudyObject.from_db(s.study_id) for s in studies]

    @staticmethod
    def get_by_lab_head(lab_head_email):
        studies = Study.objects.filter(requests__lab_head_email__contains=lab_head_email).all()
        return [StudyObject.from_db(s.study_id) for s in studies]

    @property
    def run_ids(self):
        """
        return: {"<PIPELINE_NAME>: [<LATEST_RUN>]"}
        """
        sample_object_ids = [str(s.id) for s in self.samples]
        runs = Run.objects.filter(samples__in=sample_object_ids, status=RunStatus.COMPLETED).distinct()
        return self._latest(runs)

    def _latest(self, runs):
        result = dict()
        grouped_by_pipeline = self._group_by_pipeline(runs)
        for k, v in grouped_by_pipeline.items():
            result[k] = self._filter_latest_runs(v)
        return result

    def _group_by_pipeline(self, runs):
        result = dict()
        for run in runs:
            if result.get(run.app.pipeline_name.name):
                result[run.app.pipeline_name.name].append(run)
            else:
                result[run.app.pipeline_name.name] = [run,]
        return result

    def _filter_latest_runs(self, runs):
        grouped_by_sample = dict()
        for run in runs:
            samples = [s.sample_id for s in run.samples.all()]
            samples.sort()
            key = '_'.join(samples)
            if not grouped_by_sample.get(key):
                grouped_by_sample[key] = run
            else:
                if run.created_date > grouped_by_sample[key].created_date:
                    grouped_by_sample[key] = run
        return grouped_by_sample
