import argparse
import datetime
import json
import os
import shlex
import subprocess
import sys
from contextlib import ExitStack

import portage

from .log import edie, eerror
from .tmp import get_etc_portage_tmp_file


def run_testing(job, args):
    global_features = []

    time_started = datetime.datetime.now().replace(microsecond=0).isoformat()

    emerge_cmdline = [
        "emerge",
        "--verbose",
        "y",
        "--usepkg-exclude",
        job["cp"],
        "--deep",
        "--backtrack",
        "300",
    ]
    unmerge_cmdline = [
        "emerge",
        "--rage-clean",
        job["cp"],
    ]

    if args.append_emerge:
        emerge_cmdline += shlex.split(args.append_emerge)

    if args.binpkg:
        emerge_cmdline.append("--usepkg")
        global_features.append("buildpkg")

    if args.ccache:
        if not portage.settings.get("CCACHE_DIR") or not portage.settings.get(
            "CCACHE_SIZE"
        ):
            edie("The CCACHE_DIR and/or CCACHE_SIZE is not set!")

        global_features.append("ccache")

    emerge_cmdline.append(job["cpv"])

    with ExitStack() as stack:
        tmp_files = {}

        for directory in ["env", "package.env", "package.use"]:
            tmp_files[directory] = stack.enter_context(
                get_etc_portage_tmp_file(directory, args.prefix)
            )

        tested_cpv_features = ["qa-unresolved-soname-deps", "multilib-strict"]

        if job["test_feature_toggle"]:
            tested_cpv_features.append("test")

        if tested_cpv_features:
            tmp_files["env"].write(
                'FEATURES="{}"\n'.format(" ".join(tested_cpv_features))
            )

        env_files = [os.path.basename(tmp_files["env"].name)]

        if job["extra_env_files"]:
            env_files.append(job["extra_env_files"])

        tmp_files["package.env"].write(
            "{cp} {env_files}\n".format(cp=job["cp"], env_files=" ".join(env_files))
        )

        if job["use_flags"]:
            tmp_files["package.use"].write(
                "{prefix} {flags}\n".format(
                    prefix=(
                        "*/*" if job["use_flags_scope"] == "global" else job["cpv"]
                    ),
                    flags=" ".join(job["use_flags"]),
                )
            )

        for handler in tmp_files:
            tmp_files[handler].flush()

        env = os.environ.copy()

        if args.unmerge and not args.pretend:
            subprocess.run(unmerge_cmdline, env=env)

        if args.test_feature_scope == "force":
            env["EBUILD_FORCE_TEST"] = "1"

        if global_features:
            if "FEATURES" in env:
                env["FEATURES"] = "{} {}".format(
                    env["FEATURES"], " ".join(global_features)
                )
            else:
                env["FEATURES"] = " ".join(global_features)

        emerge_result = None
        if not args.pretend:
            emerge_result = subprocess.run(emerge_cmdline, env=env)
        print("")

    return {
        "use_flags": " ".join(job["use_flags"]),
        "exit_code": 0 if emerge_result is None else emerge_result.returncode,
        "features": portage.settings.get("FEATURES"),
        "emerge_default_opts": portage.settings.get("EMERGE_DEFAULT_OPTS"),
        "emerge_cmdline": " ".join(emerge_cmdline),
        "test_feature_toggle": job["test_feature_toggle"],
        "atom": job["cpv"],
        "time": {
            "started": time_started,
            "finished": datetime.datetime.now().replace(microsecond=0).isoformat(),
        },
    }
