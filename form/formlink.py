import collections
import errno
import fcntl
import os
import select
import shlex
import subprocess
import sys

from .datapath import get_data_path

_PY3 = sys.version_info[0] >= 3
_PY32 = sys.version_info >= (3, 2, 0)

if not _PY3:
    # Python 2
    def is_string(obj):
        """Return True if the given object is a string."""
        return isinstance(obj, basestring)
else:
    # Python 3
    def is_string(obj):
        """Return True if the given object is a string."""
        return isinstance(obj, str)

def set_nonblock(fd):
    """Set the given file descriptor to non-blocking mode."""
    fcntl.fcntl(fd,
                fcntl.F_SETFL,
                fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)

class PushbackReader(object):
    """A wrapper class for streams that allows data to be pushed back into the
       stream."""

    def __init__(self, raw):
        self._raw = raw
        self._buf = ''

    def close(self):
        """Close the stream."""
        self._raw.close()

    def fileno(self):
        """Return the file descriptor."""
        return self._raw.fileno()

    def read(self):
        """Read data from the stream."""
        s = self._buf + self._raw.read()
        self._buf = ''
        return s

    def unread(self, s):
        """Push back the given string to the internal buffer, which will be used
           for the next `read()` or `read0()`."""
        self._buf = s + self._buf

    def read0(self):
        """Read the pushed-back data. No call to the underlying raw stream's
           `read()`."""
        s = self._buf
        self._buf = ''
        return s

class FormLink(object):
    """An object representing a connection to FORM."""

    # The input file for FORM.
    _INIT_FRM = get_data_path('form', 'init.frm')

    # Special keywords for communicating with FORM.
    _END_MARK = '__END__'
    _END_MARK_LEN = len(_END_MARK)
    _PROMPT = '\n__READY__\n'

    def __init__(self, args=None, keep_log=False):
        """Initialize a connection to a FORM process."""
        self._closed = True
        self._head = None
        self._log = None
        self._childpid = None
        self._formpid = None
        self._parentin = None
        self._parentout = None
        self._loggingin = None
        self.open(args, keep_log)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self, args=None, keep_log=False):
        """Open a connection to FORM.

        Open a connection to a new FORM process. The opened connection should be
        closed by `close()`. Since `open()` is called from the initializer (or
        `form.open()`), this can be guaranteed by use of the "with" statement:

        >>> import form
        >>> with form.open() as formlink:
        ...     pass  # use formlink ...

        The optional argument `args` is for the FORM command, a string or
        a sequence of strings. For example '/path/to/form' or ['tform', '-w4'].
        The default value is 'form'.

        The other argument `keep_log` indicates whether the log from FORM is
        kept and used as detailed information when an error occurs. If the value
        is >= 2, it specifies the maximum number of lines for the scrollback.
        The default value is False.

        Caveats
        -------
        In the current implementation, keep_log=True may cause a dead lock when
        the listing of the input is enabled and very long input is sent to FORM.
        """
        if args is None:
            args = 'form'

        if is_string(args):
            args = shlex.split(args)  # Split the arguments.
        elif isinstance(args, (list, tuple)):
            args = list(args)  # As a modifiable mutable object.

        self.close()

        fd_childin, fd_parentout = os.pipe()
        fd_parentin, fd_childout = os.pipe()
        fd_loggingin, fd_loggingout = os.pipe()

        pid = os.fork()
        if pid:
            # parent process
            os.close(fd_childin)
            os.close(fd_childout)
            os.close(fd_loggingout)

            parentin = os.fdopen(fd_parentin, 'r')
            parentout = os.fdopen(fd_parentout, 'w')
            loggingin = os.fdopen(fd_loggingin, 'r')

            # FORM sends 'pid\n'.
            s = parentin.readline()
            if not s:
                os.waitpid(pid, 0)
                parentin.close()
                parentout.close()
                loggingin.close()
                raise IOError('failed to read the first line from FORM')
            s = s.rstrip()
            formpid = int(s)
            # The parent must send 'pid,ppid\n'.
            s = s + ',{0}\n'.format(os.getpid())
            parentout.write(s)
            parentout.flush()
            # FORM sends 'OK' (in init.frm).
            s = parentin.read(2)
            if s != 'OK':
                os.waitpid(pid, 0)
                parentin.close()
                parentout.close()
                loggingin.close()
                raise IOError('failed to establish the connection to FORM')
            # Change the prompt.
            parentout.write('#prompt {0}\n'.format(self._PROMPT.strip()))
            # Read the first line of the FORM output.
            head = loggingin.readline().rstrip()

            set_nonblock(fd_parentin)
            set_nonblock(fd_loggingin)
            parentin = PushbackReader(parentin)
            loggingin = PushbackReader(loggingin)

            self._closed = False
            self._head = head
            if keep_log:
                if keep_log >= 2:
                    self._log = collections.deque(maxlen=keep_log)
                    self._log.append(head)
                else:
                    self._log = []
                    self._log.append(head)
            else:
                self._log = None
                # Turn off the listing of the input.
                parentout.write('#-\n')
            self._childpid = pid
            self._formpid = formpid
            self._parentin = parentin
            self._parentout = parentout
            self._loggingin = loggingin
        else:
            # child process
            os.close(fd_parentout)
            os.close(fd_parentin)
            os.close(fd_loggingin)
            os.dup2(fd_loggingout, sys.__stdout__.fileno())

            args.append('-M')
            args.append('-pipe')
            args.append('{0},{1}'.format(fd_childin, fd_childout))
            args.append(FormLink._INIT_FRM)

            if not _PY32:
                subprocess.call(args, shell=False)
            else:
                subprocess.call(args, shell=False,
                                pass_fds=(fd_childin,
                                          fd_childout,
                                          fd_loggingout))

            os.close(fd_childin)
            os.close(fd_childout)
            os.close(fd_loggingout)
            os._exit(0)

    def close(self):
        """Close the connection to FORM.

        Close the connection to the FORM process established by `open()`. The
        user should call this method after use of each FormLink object.
        """
        self._close()

    def kill(self):
        """Kill the FORM process and close the connection."""
        self._close(kill=-1)  # Kill it immediately.
#       self._close(term=-1, kill=1)

    def _close(self, term=False, kill=False):
        if not self._closed:
            try:
                # We ignore broken pipes.
                try:
                    self._parentout.write(self._PROMPT)
                    self._parentout.flush()
                except IOError as e:
                    if e.errno != errno.EPIPE:
                        raise

                if term or kill:
                    import signal
                    import time

                    # When a non-zero `term` or `kill` is given, we first wait
                    # for the child to finish within the duration. If not, stop
                    # it by SIGTERM/SIGKILL. If both `term` and `kill` are
                    # non-zero, we first try SIGTERM, and then SIGKILL.
                    # To stop the FORM process, we do not use setpgrp() and
                    # killpg() for the child, but directly use kill() for the
                    # FORM process. We expect that then the child process can
                    # finish shortly.

                    def wait(timeout):  # timeout <= 0 means no wait
                        # Wait for the child to finish.
                        t = 0.0
                        dt = 0.01
                        if timeout > 0:
                            dt = min(timeout, dt)
                        while True:
                            pid, err = os.waitpid(self._childpid, os.WNOHANG)
                            if pid:
                                return False
                            if t >= timeout:
                                return True  # still exists
                            time.sleep(dt)
                            t += dt

                    if term and kill:
                        if wait(term):
                            os.kill(self._formpid, signal.SIGTERM)
                            if wait(kill):
                                os.kill(self._formpid, signal.SIGKILL)
                                os.waitpid(self._childpid, 0)
                    else:
                        if wait(max(term, kill)):  # either term or kill is 0
                            os.kill(self._formpid,
                                    signal.SIGKILL if kill else signal.SIGTERM)
                            os.waitpid(self._childpid, 0)
                else:
                    os.waitpid(self._childpid, 0)
                self._parentin.close()
                try:
                    self._parentout.close()
                except IOError as e:
                    if e.errno != errno.EPIPE:
                        raise
                self._loggingin.close()
            finally:
                self._closed = True
                self._head = None
                self._log = None
                self._childpid = None
                self._formpid = None
                self._parentin = None
                self._parentout = None
                self._loggingin = None

    def write(self, script):
        """Send a script to FORM.

        Write the given script to the communication channel to FORM. It could
        be buffered and so FORM may not execute the sent script until `flush()`
        or `read()` is called.
        """
        if self._closed:
            raise IOError('tried to write to closed connection')
        script = script.strip()
        if script:
            self._parentout.write(script)
            self._parentout.write('\n')

    def flush(self):
        """Flush the channel to FORM.

        Flush the communication channel to FORM.
        """
        if self._closed:
            raise IOError('tried to flush closed connection')
        self._parentout.flush()

    def read(self, *names):
        """Read results from FORM.

        Wait for a response of FORM to obtain the results specified by the given
        names and return a corresponding string or (nested) list of strings.
        Objects to be read from FORM are expressions, $-variables and
        preprocessor variables.

        ========== =============================
          name       meaning
        ========== =============================
          "F"        expression F
          "$x"       $-variable $x
          "$x[]"     factorized $-variable $x
          "`A'"      preprocessor variable A
        ========== =============================

        Note that the communication for the reading is performed within the
        preprocessor of FORM (i.e., at compile-time), so one may need to write
        ".sort" to get the correct result.

        If non-string objects are passed, they are considered as sequences, and
        the return value becomes the list corresponding to the arguments. If
        a sequence is passed as the argument to this method, it is guaranteed
        that the return value is always a list:

        >>> import form
        >>> f = form.open()
        >>> f.write('''
        ...     S a1,...,a3;
        ...     L F1 = a1;
        ...     L F2 = a2;
        ...     L F3 = a3;
        ...     .sort
        ... ''')

        >>> f.read(['F1'])
        ['a1']
        >>> f.read(['F1', 'F2'])
        ['a1', 'a2']
        >>> f.read(['F1', 'F2', 'F3'])
        ['a1', 'a2', 'a3']

        A more complicated example, which returns a nested list, is

        >>> f.read('F1', ['F2', 'F3'])
        ['a1', ['a2', 'a3']]

        >>> f.close()
        """
        if self._closed:
            raise IOError('tried to read from closed connection')

        if len(names) == 1 and not is_string(names[0]):
            names = tuple(names[0])
            if len(names) == 1:
                return [self.read(*names)]  # Guarantee to return a list.
            else:
                return self.read(*names)

        if any(not is_string(x) for x in names):
            return [self.read(x) for x in names]

        for e in names:
            if len(e) >= 2 and e[0] == '`' and e[-1] == "'":
                self._parentout.write('#toexternal "{0}{1}"\n'.format(e, self._END_MARK))
            elif len(e) >= 3 and e[0] == '$' and e[-2:] == '[]':
                # Special syntax "$x[]" for factorized $-variables.
                # NOTE: (1) isfactorized($x) is zero when $x is 0 or $x has only
                #           one factor even after FactArg is performed.
                #       (2) `$x[0]' is accessible even if FactArg has not been
                #           performed. Use `$x[0]' rather than isfactorized($x).
                #       (3) `$x[1]' is not accessible (segfault) with versions
                #           before Sep  3 2015, if $x has only one factor and
                #           `$x[0]' gives 1.
                self._parentout.write((
                    "#if `${0}[0]'\n"
                    "#toexternal \"(%$)\",${0}[1]\n"
                    "#do i=2,`${0}[0]'\n"
                    "#toexternal \"*(%$)\",${0}[`i']\n"
                    "#enddo\n"
                    "#else\n"
                    "#if termsin(${0})\n"
                    "#toexternal \"%$\",${0}\n"
                    "#else\n"
                    "#toexternal \"(0)\"\n"
                    "#endif\n"
                    "#endif\n"
                    "#toexternal \"{1}\"\n"
                    ).format(e[1:-2], self._END_MARK))
            elif len(e) >= 1 and e[0] == '$':
                self._parentout.write('#toexternal "%${1}",{0}\n'.format(e, self._END_MARK))
            else:
                self._parentout.write('#toexternal "%E{1}",{0}\n'.format(e, self._END_MARK))
        self._parentout.write('#redefine FORMLINKLOOPVAR "0"')
        self._parentout.write(self._PROMPT)
        self._parentout.flush()

        result = []
        out = self._parentin.read0()
        for e in names:
            while True:
                i = out.find(self._END_MARK)
                if i >= 0:
                    result.append(out[:i])
                    out = out[i+self._END_MARK_LEN:]
                    break

                r, _, _ = select.select((self._parentin, self._loggingin),
                                        (), ())
                if self._loggingin in r:
                    s = self._loggingin.read()
                    if s:
                        i = s.rfind('\n')
                        if i >= 0:
                            msgs = s[:i].split('\n')
                            if self._log is not None:
                                self._log.extend(msgs)
                            for msg in msgs:
                                if msg.find('-->') >= 0 or msg.find('==>') >= 0:
                                    if self._log:
                                        msg += '\n'
                                        msg += '\n'.join(self._log)
                                    self.close()
                                    raise RuntimeError(msg)
                        self._loggingin.unread(s[i+1:])
                if self._parentin in r:
                    out += (self._parentin.read()
                            .replace('\n', '')
                            .replace('\\', '')
                            .replace(' ', ''))

        self._parentin.unread(out)

        if len(names) == 0:
            return None
        elif len(names) == 1:
            return result[0]
        else:
            return result

    @property
    def closed(self):
        """Return True if the connection is closed."""
        return self._closed

    @property
    def head(self):
        """Return the first line of the FORM output."""
        return self._head

    @property
    def _dateversion(self):
        import re
        if self._head:
            m = re.search(r'(?<=\()(.*)(?=\))', self._head)
            if m:
                dv = m.group(0)
                s = dv.split()
                if len(s) == 3:
                    # month
                    month_names = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
                    if s[0] in month_names:
                        m = month_names.index(s[0]) + 1
                        # date
                        if s[1].isdigit():
                            d = int(s[1])
                            if 1 <= d <= 31:
                                # year
                                if s[2].isdigit():
                                    y = int(s[2])
                                    if y >= 1:
                                        # Return an integer as "yyyymmdd".
                                        return y * 10000 + m * 100 + d
            raise ValueError('failed to parse "{0}"'.format(self._head))
        raise ValueError('no first line')
