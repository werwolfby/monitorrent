from path import path

plugins = dict()

def load_plugins(plugin_folder="plugins"):
    p = path(plugin_folder)
    for f in p.walk("*.py"):
        if f.basename() == "__init__.py":
            continue
        plugin_subpackages = filter(None, f.parent.splitall())
        module_name = '.'.join(plugin_subpackages + [f.namebase])
        __import__(module_name)

def register_plugin(type, name, instance):
    plugins.setdefault(type, dict())[name] = instance

def get_plugins(type):
    return plugins.get(type, dict()).values()
