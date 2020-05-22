import hashlib


def sha1(file_path, buffersize=1024*1024):
    try:
        hasher = hashlib.sha1()
        with open(file_path, 'rb') as f:
            contents = f.read(buffersize)
            while contents != b"":
                hasher.update(contents)
                contents = f.read(buffersize)
        return 'sha1$%s' % hasher.hexdigest().lower()
    except Exception as e:
        raise FailedToCalculateChecksum(e)


class FailedToCalculateChecksum(Exception):
    pass
