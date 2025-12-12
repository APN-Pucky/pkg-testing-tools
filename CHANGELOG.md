# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.8] - 2025-12-12

### Added

- `--depclean/-c` flag: to perform 'emerge --depclean' before each test install
- Add `--test-feature-scope=first` to run test feature toggle first
- Add `--add-sparse-use/-asu` to add one combination with minimal number of USE flags enabled that passes REQUIRED_USE (single_targets are excluded from counting)
- Add `--add-dense-use/-adu` to add one combination with maximal number of USE flags enabled that passes REQUIRED_USE (single_targets are excluded from counting)

### Changed

- Revert to running tests last unless new `--test-feature-scope=first` is set


## [0.2.7] - 2025-11-24

### Added

- `--slow` flag: to run a single thread job
- `--quiet` flag: to only show emerge output on failures
- `--oneshot/-1` flag: to not add test package to world

### Changed

- Do test run before non-test runs.
- Use python logging module instead of print

## [0.2.6] - 2024-12-04

### Added

- "perl_features_" prefix added to ignored USE flags  
- --fail-fast flag: stop testing after the first failure
- `--max-use-combinations -1` to test all possible use flag combinations

## [0.2.5] - 2024-04-19

### Added

- --pretend flag: only show the commands that would be executed
- --test-feature-scope=force also sets `EBUILD_FORCE_TEST=1`

### Changed

- `--max-use-combinations 1` is now one random use flag set instead of the default. The default is still available with `--max-use-combinations 0`

## [0.2.4] - 2024-03-16

### Fixed

- temporary repositories are only injected once
- passing no -f should not crash

### Changed

- `--file` also appends `::{repo}` to the package atom

## [0.2.3] - 2024-03-16

### Added

- -C/--unmerge flag: unmerge package before each test
- -f/--file flag: read from ebuild file and temporary inject its hosting repository

## [0.2.2] - 2024-02-17

### Added

- prefix argument

### Fixed

- swap of job definition order and temporary unmask/keyword files

## [0.2.1] - 2023-12-10

### Added

- (doc-)tests
- CI pipeline

### Changed

- Removed python/ruby targets from default ignore list
- Format/Lint code with black

## [0.2.0] - 2023-11-28

### Fixed

- cpv matching for '~category/package-version' works now

[unreleased]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.2.8...HEAD
[0.2.8]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.2.7...v0.2.8
[0.2.7]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.2.6...v0.2.7
[0.2.6]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.2.5...v0.2.6
[0.2.5]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/APN-Pucky/pkg-testing-tools/compare/v0.1.1...v0.2.0
