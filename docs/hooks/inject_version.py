from pathlib import Path
import sys


def on_config(config):
    root = Path(__file__).resolve().parents[2]

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from geonode.version import get_version

    config.setdefault("extra", {})
    config["extra"]["geonode_version"] = get_version()

    return config