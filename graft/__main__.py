import pkgutil
import sys

import graft.tools


def main(argv=None):
    print("Graft is a toolkit for working with graphs.")
    print()
    print("Available Graft Tools:")

    package = graft.tools
    prefix = package.__name__ + "."

    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        print(f"  - python -m {modname}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
