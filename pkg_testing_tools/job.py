import argparse
import datetime
import json
import os
import shlex
import subprocess
import sys
from contextlib import ExitStack
from tempfile import NamedTemporaryFile

import portage

from .log import edebug, edie, eerror, einfo
from .use import atom_to_cpv, get_package_flags, get_use_combinations


def get_package_metadata(atom):
    # This handles revisions properly, but not live ebuilds: https://bugs.gentoo.org/918693 https://github.com/APN-Pucky/pkg-testing-tools/issues/10
    cpv = atom_to_cpv(atom)
    # cpv is None on missing/masked packages
    if cpv:
        edebug(f"cpv through match(): {cpv}")
    else:
        edebug(f"could not find unmasked package {atom}, assuming it is available")
        # This handles live ebuilds properly, but not revisions: https://bugs.gentoo.org/918693 https://github.com/APN-Pucky/pkg-testing-tools/issues/10
        cpv = portage.dep.dep_getcpv(atom)
        edebug(f"cpv through dep_getcpv(): {cpv}")

    cp, version, revision = portage.versions.pkgsplit(cpv)

    iuse, ruse = get_package_flags(cpv)

    phases = portage.portdb.aux_get(cpv, ["DEFINED_PHASES"])[0].split()

    return {
        "atom": atom,
        "cp": cp,
        "cpv": cpv,
        "version": version,
        "revision": revision,
        "has_tests": ("test" in phases),
        "iuse": iuse,
        "ruse": ruse,
    }


def define_jobs(atom, args):
    jobs = []

    package_metadata = get_package_metadata(atom)

    common = {
        "cpv": atom,
        "cp": package_metadata["cp"],
        "extra_env_files": (
            " ".join(args.extra_env_file) if args.extra_env_file else []
        ),
    }

    if args.debug:
        edebug("common: {}".format(common))
        edebug("package_metadata: {}".format(package_metadata))

    if args.append_required_use:
        package_metadata["ruse"].append(args.append_required_use)

    if package_metadata["iuse"] and args.max_use_combinations > 1:
        use_combinations = get_use_combinations(
            package_metadata["iuse"],
            package_metadata["ruse"],
            args.max_use_combinations,
        )
    else:
        use_combinations = None

    if use_combinations:
        if (
            package_metadata["has_tests"] and args.test_feature_scope == "always"
        ) or args.test_feature_scope == "force":
            test_feature_toggle = True
        else:
            test_feature_toggle = False

        for flags_set in use_combinations:
            job = {}
            job.update(common)
            job.update(
                {
                    "test_feature_toggle": test_feature_toggle,
                    "use_flags": flags_set,
                    "use_flags_scope": args.use_flags_scope,
                }
            )
            jobs.append(job)

        if package_metadata["has_tests"] and args.test_feature_scope == "once":
            job = {}
            job.update(common)
            job.update(
                {
                    "test_feature_toggle": True,
                    "use_flags": [],
                    "use_flags_scope": args.use_flags_scope,
                }
            )
            jobs.append(job)
    else:
        if not package_metadata["has_tests"] or args.test_feature_scope == "never":
            job = {}
            job.update(common)
            job.update(
                {
                    "test_feature_toggle": False,
                    "use_flags": [],
                    "use_flags_scope": args.use_flags_scope,
                }
            )
            jobs.append(job)
        else:
            job = {}
            job.update(common)
            job.update({"test_feature_toggle": False, "use_flags": []})
            jobs.append(job)

            job = {}
            job.update(common)
            job.update({"test_feature_toggle": True, "use_flags": []})
            jobs.append(job)

    return jobs
