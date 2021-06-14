import os


def relative_file_name(file_name):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, file_name)


