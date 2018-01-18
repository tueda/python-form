"""Routine to get data file paths."""

import os
import pkgutil
import sys

if False:
    from typing import Optional  # noqa: F401


def get_data_path(package, resource):
    # type: (str, str) -> str
    """Return the full file path of a resource of a package."""
    loader = pkgutil.get_loader(package)
    if loader is None or not hasattr(loader, 'get_data'):
        raise PackageResourceError("Failed to load package: '{0}'".format(
            package))
    mod = sys.modules.get(package) or loader.load_module(package)
    if mod is None or not hasattr(mod, '__file__'):
        raise PackageResourceError("Failed to load module: '{0}'".format(
            package))
    parts = resource.split('/')
    parts.insert(0, os.path.dirname(mod.__file__))
    resource_name = os.path.join(*parts)
    return resource_name


class PackageResourceError(IOError):
    """Package resource not found."""
