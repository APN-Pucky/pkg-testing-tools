import pytest

from pkg_testing_tools.main import run


@pytest.mark.timeout(10)
def test_pretend_max_use():
    run(
        [
            "--test-feature-scope",
            "never",
            "--append-required-use",
            "!pgo",
            "--max-use-combinations",
            "6",
            "-p",
            "www-client/firefox",
            "--pretend",
        ]
    )
