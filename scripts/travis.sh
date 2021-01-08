#!/bin/bash

# Usage:
#   travis.sh install
#   travis.sh script
#   travis.sh after_success
#
# Environment variables:
#   TEST = test | lint
#   FORM_VERSION = 4.0 | 4.1 | 4.2 | 4.2.1

set -eu
set -o pipefail

ANSI_RED="\033[31;1m"
ANSI_RESET="\033[0m"

# Taken from https://github.com/travis-ci/travis-build/blob/master/lib/travis/build/templates/header.sh (74247a7)
travis_retry() {
  local result=0
  local count=1
  while [ $count -le 3 ]; do
    [ $result -ne 0 ] && {
      echo -e "\n${ANSI_RED}The command \"$@\" failed. Retrying, $count of 3.${ANSI_RESET}\n" >&2
    }
    # See https://gist.github.com/letmaik/caa0f6cc4375cbfcc1ff26bd4530c2a3
    # "$@"
    # result=$?
    ! { "$@"; result=$?; }
    [ $result -eq 0 ] && break
    count=$(($count + 1))
    sleep 1
  done

  [ $count -gt 3 ] && {
    echo -e "\n${ANSI_RED}The command \"$@\" failed 3 times.${ANSI_RESET}\n" >&2
  }

  return $result
}

travis_test_install() {
  # Install FORM as $(pwd)/formbin/form.
  case "$FORM_VERSION" in
    4.0)
      # v4.0-20120410 (2012-04-10)
      form_url=https://github.com/vermaseren/form/releases/download/v4.0-20120410/form-4.0-20120410-x86_64-linux.tar.gz
      ;;
    4.1)
      # v4.1-20131025 (2013-10-25)
      form_url=https://github.com/vermaseren/form/releases/download/v4.1-20131025/form-4.1-x86_64-linux.tar.gz
      ;;
    4.2)
      # v4.2.0 (2017-07-06)
      form_url=https://github.com/vermaseren/form/releases/download/v4.2.0/form-4.2.0-x86_64-linux.tar.gz
      ;;
    4.2.1)
      # v4.2.1 (2019-02-01)
      form_url=https://github.com/vermaseren/form/releases/download/v4.2.1/form-4.2.1-x86_64-linux.tar.gz
      ;;
    *)
      echo "Error: unsupported FORM_VERSION=$FORM_VERSION" >&2
      exit 1
  esac
  travis_retry wget $form_url
  tar xf $(basename $form_url)
  mv $(basename $form_url .tar.gz) formbin
  export PATH=$PATH:$(pwd)/formbin
  form -v | grep -v sec  # Print the version.

  # Get python-form installed.
  pip install .

  # For testing/code coverage.
  #case "$TRAVIS_PYTHON_VERSION" in
  #  2.6)
  #    travis_retry pip install colorama==0.3.9 coverage nose-timer==0.7.0
  #    ;;
  #  3.2)
  #    travis_retry pip install coverage==3.7.1 nose-timer
  #    ;;
  #  *)
  #    travis_retry pip install coverage nose-timer
  #    ;;
  #esac
  case "$TRAVIS_PYTHON_VERSION" in
    2.6)
      travis_retry pip install 'colorama<0.4.0' 'idna<2.8'
      # travis_retry pip install 'nose-timer<1.0.0'  # BAD ??
      # travis_retry pip install 'nose-timer<0.7.3'  # BAD ??
      #travis_retry pip install 'nose-timer<0.7.2'  # BAD??
      travis_retry pip install 'nose-timer<0.7.1'  # ??
      ;;
    3.2)
      travis_retry pip install 'coverage<4.0.0' 'coveralls<2.0.0'
      ;;
    3.4)
      travis_retry pip install 'colorama<0.4.2'
      ;;
    pypy)
      travis_retry pip install 'cryptography<3.3.0'  # OK ??
      ;;
  esac
  travis_retry pip install coveralls rednose nose-timer
}

travis_test_script() {
  export PATH=$PATH:$(pwd)/formbin
  nosetests --with-coverage --rednose --hide-skips --with-timer --timer-top-n 10
}

travis_test_after_success() {
  travis_retry coveralls
}

travis_lint_install() {
  case "$TRAVIS_PYTHON_VERSION" in
    2.*|3.0|3.1|3.2|3.3|3.4|pypy)
      travis_retry pip install flake8 flake8_docstrings pep8-naming flake8-import-order
      ;;
    *)
      travis_retry pip install flake8 flake8_docstrings pep8-naming flake8-import-order flake8-bugbear flake8-mypy
      ;;
  esac
}

travis_lint_script() {
  flake8
  case "$TRAVIS_PYTHON_VERSION" in
    2.*|3.0|3.1|3.2|3.3|3.4|pypy)
      ;;
    *)
      mypy form
      mypy -2 form
      ;;
  esac
}

travis_lint_after_success() {
  :
}

case "$TEST" in
  test|lint)
    ;;
  *)
    echo "Error: unknown TEST=$TEST" >&2
    exit 1
    ;;
esac

case "$1" in
  install|script|after_success)
    travis_${TEST}_$1
    ;;
  *)
    echo "Error: unknown command $1" >&2
    exit 1
    ;;
esac
