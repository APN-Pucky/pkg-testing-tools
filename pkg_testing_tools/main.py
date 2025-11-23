#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from contextlib import ExitStack

from .job import define_jobs
from .log import edebug, edie, eerror, einfo
from .test import run_testing
from .tmp import get_etc_portage_tmp_file


def process_args(sysargs):
    parser = argparse.ArgumentParser()

    # required = parser.add_argument_group("Required")
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-p",
        "--package-atom",
        action="append",
        default=[],
        help="Valid Portage package atom, like '=app-category/foo-1.2.3'. Can be specified multiple times to unmask/keyword all of them and test them one by one.",
    )

    group.add_argument(
        "-f",
        "--file",
        action="append",
        default=[],
        help="Portage ebuild file like 'foo-1.2.3.ebuild'. Must reside in a repository.",
    )

    optional = parser.add_argument_group("Optional")

    optional.add_argument(
        "-C",
        "--unmerge",
        action="store_true",
        required=False,
        help="Explicit unmerge before each test install.",
    )

    optional.add_argument(
        "--fail-fast",
        action="store_true",
        required=False,
        help="Exit on first failure. Useful to inspect fail logs. Default: False.",
    )

    optional.add_argument(
        "--ask",
        action="store_true",
        required=False,
        help="Ask for confirmation before executing actual tests.",
    )

    optional.add_argument(
        "--pretend",
        "--dry-run",
        action="store_true",
        required=False,
        help="Do not execute the tests.",
    )

    optional.add_argument(
        "--binpkg",
        action="store_true",
        required=False,
        help="Append --usepkg to emerge command and add buildpkg to FEATURES.",
    )

    optional.add_argument(
        "--ccache", action="store_true", required=False, help="Add ccache to FEATURES."
    )

    optional.add_argument(
        "--append-required-use",
        action="store",
        type=str,
        required=False,
        help="Append REQUIRED_USE entries, useful for blacklisting flags, like '!systemd !libressl' on systems that runs neither. The more complex REQUIRED_USE, the longer it take to get USE flags combinations.",
    )

    optional.add_argument(
        "--max-use-combinations",
        action="store",
        type=int,
        required=False,
        default=16,
        help="Generate up to N combinations of USE flags, the combinations are random out of those which pass check for REQUIRED_USE. Default: 16.",
    )

    optional.add_argument(
        "--use-flags-scope",
        action="store",
        type=str,
        required=False,
        default="local",
        choices=["local", "global"],
        help="Local sets USE flags for package specified by atom, global sets flags for */*.",
    )

    optional.add_argument(
        "--test-feature-scope",
        action="store",
        type=str,
        required=False,
        default="once",
        choices=["once", "always", "force", "never"],
        help="Enables FEATURES='test' once, for default use flags, always, for every run or never. force also sets EBUILD_FORCE_TEST=1. Default: 'once'.",
    )

    optional.add_argument(
        "--report",
        action="store",
        type=str,
        required=False,
        help="Save report in JSON format under specified path.",
    )

    optional.add_argument(
        "--slow",
        action="store_true",
        required=False,
        help="Run tests in slow mode, which takes more time.",
        default=False,
    )

    optional.add_argument(
        "--prefix",
        action="store",
        default="",
        type=str,
        required=False,
        help="Set the prefix for the portage configuration files. Default: ''.",
    )

    optional.add_argument(
        "--debug",
        action="store_true",
        required=False,
        help="Enable debug output, like printing emerge command line.",
        default=False,
    )

    optional.add_argument(
        "--extra-env-file",
        action="append",
        type=str,
        required=False,
        help="Extra /etc/portage/env/ file name, to be used while testing packages. Can be passed multile times.",
    )

    optional.add_argument(
        "--oneshot",
        "-1",
        action="store_true",
        default=False,
        required=False,
        help="Shortcut to append --oneshot/-1 to emerge command.",
    )

    optional.add_argument(
        "--append-emerge",
        action="store",
        type=str,
        required=False,
        help="Append flags or parameters to the actual emerge call.",
    )

    args, extra_args = parser.parse_known_args(sysargs)
    if extra_args:
        if extra_args[0] != "--":
            parser.error(
                "Custom arguments that are meant to be passed to pkg-testing-tool are to be palced after '--'."
            )
        extra_args.remove("--")

    if len(sysargs) == 0:
        parser.print_help(sys.stderr)
        sys.exit(1)
    if args.debug:
        edebug("{}".format(args))
    return args, extra_args


def yes_no(question):
    reply = input(question).lower()

    if reply == "y":
        return True

    return False


def pkg_testing_tool(args, extra_args):
    results = []

    # Unconditionally unmask and keyword packages selected by atom.
    # No much of a reason to check what arch we're running or if package is masked in first place.
    with ExitStack() as stack:
        tmp_files = {}

        for directory in ["package.accept_keywords", "package.unmask", "repos.conf"]:
            tmp_files[directory] = stack.enter_context(
                get_etc_portage_tmp_file(directory, args.prefix)
            )

        repos = []
        for ebuild in args.file:
            # test that file ends in ".ebuild"
            if not ebuild.endswith(".ebuild"):
                edie("File {} does not end with '.ebuild'.".format(ebuild))
            repo = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(ebuild)))
            )
            # read repo_name from repo profiles/repo_name
            repo_name = "zzzpkgtestingtool"
            with open(os.path.join(repo, "profiles/repo_name"), "r") as f:
                repo_name = f.read().strip()
            # only add repo once
            if repo_name not in repos:
                repos += [repo_name]
                tmp_files["repos.conf"].write(
                    f"[{repo_name}]\npriority=9999\nlocation = {repo}\n"
                )
            # ebuild to category/package-X.Y.Z
            # get parent directory name of ebuild
            category = os.path.basename(
                os.path.dirname(os.path.dirname(os.path.abspath(ebuild)))
            )
            package_version = os.path.basename(ebuild).replace(".ebuild", "")
            args.package_atom += [
                "=" + category + "/" + package_version + "::" + repo_name
            ]
            # make sure we have the right manifest already
            if args.debug:
                edebug(f"ebuild {ebuild} manifest")
            subprocess.run(["ebuild", ebuild, "manifest"])

        jobs = []

        for atom in args.package_atom:
            # Unmask and keyword all the packages prior to testing them.
            tmp_files["package.accept_keywords"].write("{atom} **\n".format(atom=atom))
            tmp_files["package.unmask"].write("{atom}\n".format(atom=atom))

        for handler in tmp_files:
            tmp_files[handler].flush()

        for atom in args.package_atom:
            for new_job in define_jobs(atom, args):
                jobs.append(new_job)

        padding = max(len(i["cpv"]) for i in jobs) + 3

        einfo("Following testing jobs will be executed:")
        for job in jobs:
            print(
                "{cpv:<{padding}} USE: {use_flags}{test_feature}".format(
                    cpv=job["cpv"],
                    use_flags=(
                        "<default flags>"
                        if not job["use_flags"]
                        else " ".join(job["use_flags"])
                    ),
                    test_feature=(
                        ", FEATURES: test" if job["test_feature_toggle"] else ""
                    ),
                    padding=padding,
                )
            )

        if args.ask:
            if not yes_no(">>> Do you want to continue? [y/N]: "):
                sys.exit(1)

        i = 0
        for job in jobs:
            i += 1
            einfo(
                "Running ({i} of {max_i}) {cpv} with USE: {use_flags}{test_feature}".format(
                    i=i,
                    max_i=len(jobs),
                    cpv=job["cpv"],
                    use_flags=(
                        "<default flags>"
                        if not job["use_flags"]
                        else " ".join(job["use_flags"])
                    ),
                    test_feature=(
                        ", FEATURES: test" if job["test_feature_toggle"] else ""
                    ),
                )
            )
            results.append(run_testing(job, args))
            if args.fail_fast and results[-1]["exit_code"] != 0:
                eerror("Exiting due to --fail-fast.")
                break

    failures = []
    for item in results:
        if item["exit_code"] != 0:
            failures.append(item)

    if args.report:
        with open(args.report, "w") as report:
            report.write(json.dumps(results, indent=4, sort_keys=True))

    if len(failures) > 0:
        eerror("Not all runs were successful.")
        for entry in failures:
            print(
                "atom: {atom}, USE flags: '{use_flags}'".format(
                    atom=entry["atom"], use_flags=entry["use_flags"]
                )
            )
        sys.exit(1)
    else:
        einfo("All good.")


def run(sysargs):
    args, extra_args = process_args(sysargs)
    pkg_testing_tool(args, extra_args)


def main():
    run(sys.argv[1:])


if __name__ == "__main__":
    main()
