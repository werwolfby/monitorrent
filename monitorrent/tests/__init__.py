import os
import vcr
import vcr.cassette
import functools
import inspect

test_vcr = vcr.VCR(
    cassette_library_dir=os.path.join(os.path.dirname(__file__), "cassettes"),
    record_mode="once"
)


def use_vcr(func=None, **kwargs):
    if func is None:
        # When called with kwargs, e.g. @use_vcr(inject_cassette=True)
        return functools.partial(use_vcr, **kwargs)
    module = func.__module__.split('tests.')[-1]
    class_name = inspect.stack()[1][3]
    cassette_name = '.'.join([module, class_name, func.__name__])
    kwargs.setdefault('path', cassette_name)
    return test_vcr.use_cassette(**kwargs)(func)
