class SampleStatus(object):
    def __init__(self, sample_id, igocomplete, code, status, message):
        self.sample_id = sample_id
        self.igocomplete = igocomplete
        self.code = code
        self.status = status
        self.message = message

    def __str__(self):
        return f"SampleStatus(sample_id={self.sample_id}, code={self.code}, message={self.message})"

    def to_dict(self):
        return {
            "type": "SAMPLE",
            "sample": self.sample_id,
            "igocomplete": self.igocomplete,
            "status": self.status,
            "message": self.message,
            "code": self.code,
        }
