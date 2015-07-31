"""A module to run FORM programs from Python."""

import fcntl
import os
import pkgutil
import select
import shlex
import signal
import subprocess
import sys

_PY3 = sys.version_info[0] >= 3
_PY32 = sys.version_info >= (3, 2, 0)

if not _PY3:
    # Python 2.*
    def is_string(obj):
        """Returns true if the given object is a string."""
        return isinstance(obj, basestring)
else:
    # Python 3.*
    def is_string(obj):
        """Returns true if the given object is a string."""
        return isinstance(obj, str)

def get_data_path(package, resource):
    """Returns the full file path of a resource of a package."""
    loader = pkgutil.get_loader(package)
    if loader is None or not hasattr(loader, 'get_data'):
        return None
    mod = sys.modules.get(package) or loader.load_module(package)
    if mod is None or not hasattr(mod, '__file__'):
        return None
    parts = resource.split('/')
    parts.insert(0, os.path.dirname(mod.__file__))
    resource_name = os.path.join(*parts)
    return resource_name

def set_nonblock(fd):
    """Sets the non-block descriptor flag for the given file descriptor."""
    fcntl.fcntl(fd,
                fcntl.F_SETFL,
                fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)

class BufferedReader(object):
    """A wrapper class of file objects for buffered reading."""

    def __init__(self, f):
        self._f = f
        self._buf = ''

    def close(self):
        """Closes the file."""
        self._f.close()

    def fileno(self):
        """Returns the file descriptor."""
        return self._f.fileno()

    def read(self, size=None):
        """Reads from the file."""
        if size is None or size < 0:
            s = self._buf + self._f.read()
            self._buf = ''
            return s
        else:
            if size <= len(self._buf):
                s = self._buf[:size]
                self._buf = self._buf[size:]
                return s
            else:
                s = self._buf + self._f.read(size - len(self._buf))
                self._buf = ''
                return s

    def unread(self, s):
        """Pushes back the given string to the buffer that is used for the next
        read()."""
        self._buf = s + self._buf

    def read_buffer(self):
        """Reads the pushed-back data."""
        s = self._buf
        self._buf = ''
        return s

class FormLink(object):
    """A class for representing a connection to FORM."""

    # The input file for FORM.
    _INIT_FRM = get_data_path('form', 'init.frm')

    def __init__(self, args=None):
        """Initializes a connection to a FORM process."""
        self._closed = True
        self._childpid = None
        self._parentin = None
        self._parentout = None
        self._loggingin = None
        self.open(args)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self, args=None):
        """Opens a connection to FORM.

        Opens a connection to a FORM process. The opened connection should be
        closed by close(). Since open() is called from the initializer (or
        form.open()), this can be guaranteed by use of the "with" statement:

            with form.open() as formlink:
                # use formlink ...

        The optional argument "args" is for the FORM command, a string or
        a sequence of strings. For example '/path/to/form' or ['tform', '-w4'].
        The default value is 'form'.
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
                os.kill(pid, signal.SIGKILL)
                parentin.close()
                parentout.close()
                loggingin.close()
                raise IOError('failed to read the first line from FORM')
            # The parent must send 'pid,ppid\n'.
            s = s.rstrip() + ',{0}\n'.format(os.getpid())
            parentout.write(s)
            parentout.flush()
            # FORM sends 'OK' (in init.frm).
            s = parentin.read(2)
            if s != 'OK':
                os.kill(pid, signal.SIGKILL)
                parentin.close()
                parentout.close()
                loggingin.close()
                raise IOError('failed to establish the connection to FORM')

            set_nonblock(fd_parentin)
            set_nonblock(fd_loggingin)
            parentin = BufferedReader(parentin)
            loggingin = BufferedReader(loggingin)

            self._closed = False
            self._childpid = pid
            self._parentin = parentin
            self._parentout = parentout
            self._loggingin = loggingin
        else:
            # child process
            os.close(fd_parentout)
            os.close(fd_parentin)
            os.close(fd_loggingin)
            os.dup2(fd_loggingout, sys.__stdout__.fileno())

            args.append('-q')
            args.append('-M')
            args.append('-pipe')
            args.append('{0},{1}'.format(fd_childin, fd_childout))
            args.append(FormLink._INIT_FRM)

            if not _PY32:
                subprocess.call(args, shell=False)
            else:
                subprocess.call(args, shell=False,
                                pass_fds=(fd_childin, fd_childout, fd_loggingout))

            os.close(fd_childin)
            os.close(fd_childout)
            os.close(fd_loggingout)
            sys.exit()

    def close(self):
        """Closes the connection to FORM.

        Closes the connection to a FORM process established by open(). The user
        should call this method after use of FormLink objects.
        """
        if not self._closed:
            self._parentout.write('\n\n')
            self._parentout.flush()
            # XXX: better to use waitpid for a little while?
            self._parentin.close()
            self._parentout.close()
            self._loggingin.close()
            os.kill(self._childpid, signal.SIGKILL)

            self._closed = True
            self._childpid = None
            self._parentin = None
            self._parentout = None
            self._loggingin = None

    def write(self, script):
        """Sends a script to FORM.

        Writes the given script to the communication channel to FORM. FORM does
        not execute the sent script until flush() or read() is called.
        """
        if self._closed:
            raise IOError('tried to write to closed connection')
        script = script.strip()
        if script:
            self._parentout.write(script)
            self._parentout.write('\n')

    def flush(self):
        """Flushes the channel to FORM.

        Flushes the communication channel to FORM and asks FORM to execute the
        sent script.
        """
        if self._closed:
            raise IOError('tried to flush closed connection')
        self._parentout.write('#fromexternal\n\n')
        self._parentout.flush()

    def read(self, *names):
        """Reads results from FORM.

        Asks FORM to execute the sent script and waits for a response of FORM to
        obtain the results specified by the given names. The object to be read
        from FORM are expressions (e.g., "F"), $-variables ("$x") and
        preprocessor variables ("`VAR'"). Note that the communication from FORM
        is done in the preprocessor of FORM (i.e., at compile-time), so one may
        need to write ".sort" to get the correct result. The return value is
        a string, or a tuple of strings when multiple names are passed.
        """
        if self._closed:
            raise IOError('tried to read from closed connection')

        END_MARK = '__END__'
        END_MARK_LEN = len(END_MARK)

        for e in names:
            if len(e) > 0 and e[0] == '`' and e[-1] == "'":
                self._parentout.write('#toexternal "{0}{1}"\n'.format(e, END_MARK))
            elif len(e) > 0 and e[0] == '$':
                self._parentout.write('#toexternal "%${1}", {0}\n'.format(e, END_MARK))
            else:
                self._parentout.write('#toexternal "%E{1}", {0}\n'.format(e, END_MARK))
        self._parentout.write('#fromexternal\n\n')
        self._parentout.flush()

        result = []
        out = self._parentin.read_buffer()
        for e in names:
            while True:
                i = out.find(END_MARK)
                if i >= 0:
                    result.append(out[:i])
                    out = out[i+END_MARK_LEN:]
                    break

                r, _, _ = select.select((self._parentin, self._loggingin),
                                        (), ())
                if self._loggingin in r:
                    s = self._loggingin.read()
                    if s:
                        i = s.rfind('\n')
                        if i >= 0:
                            for msg in s[:i].split('\n'):
                                if msg.find('-->') >= 0 or msg.find('==>') >= 0:
                                    self.close()
                                    raise RuntimeError(msg)
                        self._loggingin.unread(s[i+1:])
                if self._parentin in r:
                    out += self._parentin.read().replace('\n', '').replace(' ', '')

        self._parentin.unread(out)

        if len(names) == 0:
            return None
        elif len(names) == 1:
            return result[0]
        else:
            return tuple(result)

    @property
    def closed(self):
        """Returns true if the connection is closed."""
        return self._closed

def open(args=None):
    """Opens a connection to FORM and returns a link object."""
    return FormLink(args)
