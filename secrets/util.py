import os


def getenv_or_error(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f'env var {name} must be defined')
    return value
