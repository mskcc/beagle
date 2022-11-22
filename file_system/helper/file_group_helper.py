from file_system.models import FileGroup


def default_file_group():
    return str(FileGroup.objects.filter(default=True).first().id)


def get_user_file_groups(user):
    return FileGroup.objects.filter(owner=user).all()
