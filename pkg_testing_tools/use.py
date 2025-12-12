#!/usr/bin/env python3

import itertools
import random
from typing import Iterable

import portage


def iuse_match_always_true(flag):
    """
    Dummy function to pass to portage.dep.check_required_use().
    """
    return True


def strip_use_flags(flags):
    """
    Remove the leading + or - from use flags.

    :param flags: list of use flags
    :return: list of use flags without the leading + or -

    >>> strip_use_flags(["-flag1", "+flag2", "flag3"])
    ['flag1', 'flag2', 'flag3']
    """
    stripped_flags = []

    for flag in flags:
        if flag[0] in ["+", "-"]:
            flag = flag[1:]

        stripped_flags.append(flag)

    return stripped_flags


def filter_out_use_flags(flags):
    """
    Remove use flags that we don't want to test.

    :param flags: list of use flags
    :return: list of use flags without the ones we don't want to test

    >>> filter_out_use_flags(["flag1", "flag2", "debug"])
    ['flag1', 'flag2']
    """
    new_flags = []

    ignore_flags_with_prefix = (
        "abi_",
        "cpu_flags_",
        "eglibc_",
        "elibc_",
        "kernel_",
        "l10n_",
        "linguas_",
        "perl_features_",
        # "python_target_",
        # "python_targets_",
        # "ruby_targets_",
        "video_cards_",
    )

    ignore_flags = set(["debug", "doc", "test", "selinux", "split-usr", "pic"])

    # some flags that *most* likely we shouldn't shuffle and test.
    for flag in flags:
        if not flag.startswith(ignore_flags_with_prefix) and flag not in ignore_flags:
            new_flags.append(flag)

    return new_flags


def atom_to_cpv(atom):
    """
    Get the cpv for an atom.
    """

    matched = portage.db[portage.root]["porttree"].dbapi.match(atom)

    if len(matched) == 0:
        return None
    return matched[0]


def get_package_flags(cpv):
    """
    Get the use flags and required use flags for a package.
    """
    flags = portage.db[portage.root]["porttree"].dbapi.aux_get(
        cpv, ["IUSE", "REQUIRED_USE"]
    )
    use_flags = strip_use_flags(flags[0].split())
    use_flags = filter_out_use_flags(use_flags)
    use_flags = sorted(use_flags)

    ruse_flags = flags[1].split()

    return [use_flags, ruse_flags]


def yield_use_flags_toggles_sorted(
    iuse: list[str],
    inverted: bool = False,
) -> Iterable[list[str]]:
    """
    Generate use flag combinations sorted by number of enabled flags.
    Much faster than looping through all combinations.

    This function is needed for finding the dense/sparse use flags when there are many use flags (e.g. firefox).

    :param iuse: list of use flags
    :param inverted: whether to invert the toggling logic (False for sparse, True for dense)
    :return: iterator yielding use flag combinations sorted by number of enabled flags
    """

    str_enabled = "" if not inverted else "-"
    str_disabled = "-" if not inverted else ""
    n = len(iuse)
    for k in range(n + 1):
        for ones_pos in itertools.combinations(range(n), k):
            vec = [str_disabled] * n
            for i in ones_pos:
                vec[i] = str_enabled
            yield list("".join(flag) for flag in list(zip(vec, iuse)))


def yield_use_flags_toggles_sorted_split(
    iuse_sorted: list[str],
    iuse_unsorted: list[str],
    inverted: bool = False,
) -> Iterable[list[str]]:
    for sorted_uses in yield_use_flags_toggles_sorted(iuse_sorted, inverted):
        for unsorted_uses in yield_use_flags_toggles_sorted(iuse_unsorted, inverted):
            yield sorted_uses + unsorted_uses


def get_use_flags_toggles(
    index: int, iuse: list[str], inverted: bool = False
) -> list[str]:
    """
    Toggle use flags based on the index.

    :param index: index of the use flag combination
    :param iuse: list of use flags
    :param inverted: whether to invert the toggling logic
    :return: list of use flags with the toggled flags

    >>> get_use_flags_toggles(0, ["flag1", "flag2", "flag3"])
    ['-flag1', '-flag2', '-flag3']
    >>> get_use_flags_toggles(1, ["flag1", "flag2", "flag3"])
    ['flag1', '-flag2', '-flag3']
    >>> get_use_flags_toggles(2, ["flag1", "flag2", "flag3"])
    ['-flag1', 'flag2', '-flag3']
    >>> get_use_flags_toggles(3, ["flag1", "flag2", "flag3"])
    ['flag1', 'flag2', '-flag3']
    >>> get_use_flags_toggles(4, ["flag1", "flag2", "flag3"])
    ['-flag1', '-flag2', 'flag3']
    >>> get_use_flags_toggles(7, ["flag1", "flag2", "flag3"])
    ['flag1', 'flag2', 'flag3']
    >>> get_use_flags_toggles(0, ["flag1", "flag2", "flag3"], inverted=True)
    ['flag1', 'flag2', 'flag3']
    >>> get_use_flags_toggles(4, ["flag1", "flag2", "flag3"], inverted=True)
    ['flag1', 'flag2', '-flag3']
    """
    on_off_switches = []
    str_enabled = "" if not inverted else "-"
    str_disabled = "-" if not inverted else ""

    for i in range(len(iuse)):
        if (2**i) & index:
            on_off_switches.append(str_enabled)
        else:
            on_off_switches.append(str_disabled)

    flags = list("".join(flag) for flag in list(zip(on_off_switches, iuse)))

    return flags


def get_use_combinations(
    iuse: list[str],
    ruse: list[str],
    max_use_combinations: int,
    add_sparse_use: bool = False,
    add_dense_use: bool = False,
) -> list[list[str]]:
    """
    Iterate through all possible use flag combinations and return the ones that satisfy the required use constraints specified by the ruse parameter.

    :param iuse: list of use flags
    :param ruse: list of required use flags
    :param max_use_combinations: maximum number of use flag combinations to return
    :param add_sparse_use: add the combination with the fewest enabled USE flags that satisfies constraints
    :param add_dense_use: add the combination with the most enabled USE flags that satisfies constraints
    :return: list of valid use flag combinations

    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["flag1"], 999)
    [['flag1', '-flag2', '-flag3'], ['flag1', 'flag2', '-flag3'], ['flag1', '-flag2', 'flag3'], ['flag1', 'flag2', 'flag3']]
    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["-flag1"], 999)
    [['-flag1', '-flag2', '-flag3'], ['-flag1', 'flag2', '-flag3'], ['-flag1', '-flag2', 'flag3'], ['-flag1', 'flag2', 'flag3']]
    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["!flag1"], 999)
    [['-flag1', '-flag2', '-flag3'], ['-flag1', 'flag2', '-flag3'], ['-flag1', '-flag2', 'flag3'], ['-flag1', 'flag2', 'flag3']]
    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["!flag1"], 2, False, True) # doctest: +ELLIPSIS
    [['-flag1', 'flag2', 'flag3'], ['-flag1', ...]]
    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["!flag1"], 3, True, True) # doctest: +ELLIPSIS
    [['-flag1', '-flag2', '-flag3'], ['-flag1', 'flag2', 'flag3'], ['-flag1', ...]]
    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["!flag1"], 1, True, False)
    [['-flag1', '-flag2', '-flag3']]
    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["!flag1"], 1, False, True)
    [['-flag1', 'flag2', 'flag3']]

    """
    all_combinations_count = 2 ** len(iuse)

    valid_use_flags_combinations = []

    if add_sparse_use:
        for flags in yield_use_flags_toggles_sorted_split(
            [use for use in iuse if "single_target" not in use],
            [use for use in iuse if "single_target" in use],
            False,
        ):
            if (
                flags not in valid_use_flags_combinations
                and portage.dep.check_required_use(
                    " ".join(ruse), flags, iuse_match_always_true
                )
            ):
                valid_use_flags_combinations.append(flags)
                break  # early quit O(2^n) loop

    if add_dense_use:
        for flags in yield_use_flags_toggles_sorted_split(
            [use for use in iuse if "single_target" not in use],
            [use for use in iuse if "single_target" in use],
            True,
        ):
            if (
                flags not in valid_use_flags_combinations
                and portage.dep.check_required_use(
                    " ".join(ruse), flags, iuse_match_always_true
                )
            ):
                valid_use_flags_combinations.append(flags)
                break  # early quit O(2^n) loop

    if max_use_combinations >= 0 and all_combinations_count > max_use_combinations:
        random.seed()
        checked_combinations = set()

        while (
            len(valid_use_flags_combinations) < max_use_combinations
            and len(checked_combinations) < all_combinations_count
        ):
            index = random.randint(0, all_combinations_count - 1)

            if index in checked_combinations:
                continue
            else:
                checked_combinations.add(index)

            flags = get_use_flags_toggles(index, iuse)

            if (
                flags not in valid_use_flags_combinations
                and portage.dep.check_required_use(
                    " ".join(ruse), flags, iuse_match_always_true
                )
            ):
                valid_use_flags_combinations.append(flags)
    else:
        for index in range(0, all_combinations_count):
            flags = get_use_flags_toggles(index, iuse)

            if (
                flags not in valid_use_flags_combinations
                and portage.dep.check_required_use(
                    " ".join(ruse), flags, iuse_match_always_true
                )
            ):
                valid_use_flags_combinations.append(flags)

    return valid_use_flags_combinations
