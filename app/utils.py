import importlib
import pkgutil


def import_all_modules(package):
    """Recursively import all modules in a package."""
    for _, module_name, is_pkg in pkgutil.iter_modules(
        package.__path__, package.__name__ + "."
    ):
        importlib.import_module(module_name)
