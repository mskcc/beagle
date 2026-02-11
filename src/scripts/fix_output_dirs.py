import os
import shutil


def sync_dir(src, dst):
    if os.path.isfile("src"):
        return
    src_dirs = os.listdir(src)
    dst_dirs = os.listdir(dst)
    for d in src_dirs:
        if not d in dst_dirs:
            if os.path.isfile(os.path.join(src, d)):
                shutil.copy2(os.path.join(src, d), os.path.join(dst, d))
            else:
                shutil.copytree(os.path.join(src, d), os.path.join(dst, d))
        else:
            sync_dir(os.path.join(src, d), os.path.join(dst, d))


def list_requests(path):
    reqs = os.listdir(path)
    for r in reqs:
        if os.listdir(os.path.join(path, r)):
            if "21.4.4" in os.listdir(os.path.join(path, r)):
                sync_dir(os.path.join(path, r, "21.4.4"), os.path.join(path, r, "1.1.2"))
