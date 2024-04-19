# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


### Added

- --pretend flag: only show the commands that would be executed
- --test-feature-scope=force also sets EBUILD_FORCE_TEST=1

### Changed

- `--max-use-combinations 1` is now one random use flag set instead of the default. The default is still availbale with `--max-use-combinations 0`

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

[unreleased]: https://github.com/APN-Pucky/pkg-testing-tools/compare/0.2.4...HEAD
[0.2.4]: https://github.com/APN-Pucky/pkg-testing-tools/compare/0.2.3...0.2.4
[0.2.3]: https://github.com/APN-Pucky/pkg-testing-tools/compare/0.2.2...0.2.3
[0.2.2]: https://github.com/APN-Pucky/pkg-testing-tools/compare/0.2.1...0.2.2
[0.2.1]: https://github.com/APN-Pucky/pkg-testing-tools/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/APN-Pucky/pkg-testing-tools/compare/0.1.1...0.2.0
