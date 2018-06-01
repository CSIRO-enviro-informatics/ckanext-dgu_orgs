from ckan.plugins import toolkit

from ckan import __version__ as ckan__version__

# encoding: utf-8
try:
    try:
        import packaging # direct use
    except ImportError:
        # v39.0 and above.
        try:
            from setuptools.extern import packaging
        except ImportError:
            # Before v39.0
            from pkg_resources.extern import packaging
    version = packaging.version
except ImportError:
    raise RuntimeError("The 'packaging' library is missing.")

ckan_version = version.parse(ckan__version__)

def is_ckan_2_8_0():
    if ckan_version >= version.parse("2.8.0"):
        return True
    return False


def is_bootstrap_2():
    config = toolkit.config
    try:
        base_templates = config["ckan.base_templates_folder"]
    except (KeyError, AttributeError, IndexError):
        base_templates = None
    try:
        base_public = config["ckan.base_public_folder"]
    except (KeyError, AttributeError, IndexError):
        base_public = None
    if (base_public and "bs2" in base_public) or \
            (base_templates and "bs2" in base_templates):
        return True
    if base_templates is None and base_public is None:
        # CKAN 2.8.0 defaults to bootstrap3
        return not bool(is_ckan_2_8_0())
    return False

__all__ = ['version', 'ckan_version', 'is_bootstrap_2', 'is_ckan_2_8_0']
