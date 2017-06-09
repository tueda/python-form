# Change Log

## Unreleased

### Changed

- `FormError` is raised when `FormLink.read()` finds the FORM process stopped by
  some error (previously `RuntimeError`).
  ([1e1ae33](https://github.com/tueda/python-form/commit/1e1ae33))

[Full changes...](https://github.com/tueda/python-form/compare/v0.2.1...HEAD)

## [0.2.1](https://github.com/tueda/python-form/releases/tag/v0.2.1) (2017-05-31)

- This version came with document enhancement.

[Full changes...](https://github.com/tueda/python-form/compare/v0.2.0...v0.2.1)

## [0.2.0](https://github.com/tueda/python-form/releases/tag/v0.2.0) (2017-05-14)

### Changed

- The default executable name of FORM can be configured by the environment
  variable `$FORM`.
  ([bc91b14](https://github.com/tueda/python-form/commit/bc91b14))

- Destructor was added for `form.FormLink`.
  ([ac5babe](https://github.com/tueda/python-form/commit/ac5babe))

### Performance Improvement

- Faster reading from FORM for long expressions.
  ([a5131bf](https://github.com/tueda/python-form/commit/a5131bf))

[Full changes...](https://github.com/tueda/python-form/compare/v0.1.0...v0.2.0)

## [0.1.0](https://github.com/tueda/python-form/releases/tag/v0.1.0) (2015-09-19)

First release.
