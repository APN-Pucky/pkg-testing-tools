#!/usr/bin/env python3

import random

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
        "elibc_",
        "eglibc_",
        "video_cards_",
        "linguas_",
        "l10n_",
        "kernel_",
        "abi_",
        # "python_target_",
        # "python_targets_",
        # "ruby_targets_",
        "cpu_flags_",
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
        # TODO raise for now, but better handling might be better :/
        raise Exception("Atom not found, typo?")
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


def get_use_flags_toggles(index, iuse):
    """
    Toggle use flags based on the index.

    :param index: index of the use flag combination
    :param iuse: list of use flags
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
    """
    on_off_switches = []

    for i in range(len(iuse)):
        if (2**i) & index:
            on_off_switches.append("")
        else:
            on_off_switches.append("-")

    flags = list("".join(flag) for flag in list(zip(on_off_switches, iuse)))

    return flags


def get_use_combinations(iuse, ruse, max_use_combinations):
    """
    Iterate through all possible use flag combinations and return the ones that

    :param iuse: list of use flags
    :param ruse: list of required use flags
    :param max_use_combinations: maximum number of use flag combinations to return
    :return: list of valid use flag combinations

    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["flag1"], 999)
    [['flag1', '-flag2', '-flag3'], ['flag1', 'flag2', '-flag3'], ['flag1', '-flag2', 'flag3'], ['flag1', 'flag2', 'flag3']]
    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["-flag1"], 999)
    [['-flag1', '-flag2', '-flag3'], ['-flag1', 'flag2', '-flag3'], ['-flag1', '-flag2', 'flag3'], ['-flag1', 'flag2', 'flag3']]
    >>> get_use_combinations(["flag1", "flag2", "flag3"], ["!flag1"], 999)
    [['-flag1', '-flag2', '-flag3'], ['-flag1', 'flag2', '-flag3'], ['-flag1', '-flag2', 'flag3'], ['-flag1', 'flag2', 'flag3']]

    """
    all_combinations_count = 2 ** len(iuse)

    valid_use_flags_combinations = []

    if all_combinations_count > max_use_combinations:
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

            if portage.dep.check_required_use(
                " ".join(ruse), flags, iuse_match_always_true
            ):
                valid_use_flags_combinations.append(flags)
    else:
        for index in range(0, all_combinations_count):
            flags = get_use_flags_toggles(index, iuse)

            if portage.dep.check_required_use(
                " ".join(ruse), flags, iuse_match_always_true
            ):
                valid_use_flags_combinations.append(flags)

    return valid_use_flags_combinations
