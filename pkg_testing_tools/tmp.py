import logging
import os
import sys
from tempfile import NamedTemporaryFile


def get_etc_portage_tmp_file(directory_name, prefix):
    target_location = os.path.join(prefix + "/etc/portage", directory_name)

    if not os.path.isdir(target_location):
        logging.critical(
            "The location {} needs to exist and be a directory".format(target_location)
        )
        sys.exit(1)

    handler = NamedTemporaryFile(
        mode="w", prefix="zzz_pkg_testing_tool_", dir=target_location
    )

    umask = os.umask(0)
    os.umask(umask)
    os.chmod(handler.name, 0o644 & ~umask)

    return handler
