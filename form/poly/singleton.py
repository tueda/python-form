"""Singleton."""

from .. import formlink
from ..six import string_types


class FormSingleton(formlink.FormLink):
    """Customized FormLink for a singleton."""

    def __init__(self):
        """Construct a link to FORM."""
        self._instance_counter = 0
        self._id_prefix = None
        self._id_next = 0
        self._id_pool = []
        self._hooks = []
        super(FormSingleton, self).__init__()

    def open(self, *args, **kwargs):
        """Open a connection."""
        super(FormSingleton, self).open(*args, **kwargs)
        self._init_instance()

    def _init_instance(self):
        """Additional initialization at each opening of the connection."""
        self.check()

        self._instance_counter += 1
        self._id_next = 0
        self._id_pool = []

        # Put the FORM process ID and instance ID to the prefix to avoid
        # possible confusion with closed/other connections.
        self._id_prefix = '$x{0}x'.format(self._formpid)
        if self._instance_counter > 1:
            self._id_prefix += '{0}x'.format(self._instance_counter)

        # Execute the installed hooks. Each hook is a str or a function.
        if self._hooks:
            for f in self._hooks:
                if isinstance(f, string_types):
                    self.write(f)
                else:
                    f(self)
            self.check()

    def install_hook(self, h):
        """Install a hook to be executed for every connection."""
        if h in self._hooks:
            return
        self._hooks.append(h)
        if not self.closed:
            if isinstance(h, string_types):
                self.write(h)
            else:
                h(self)
            self.check()

    def check(self):
        """Check if any FORM error occurred."""
        self.write('#$ok=1;')
        if self.read('$ok') != '1':
            # If something goes wrong, usually ``read()`` raises an error and
            # the next line is not executed.
            raise RuntimeError('FORM returned $ok != 1')

    def next_id(self):
        """Return the next unique ID for a $-variable."""
        if self._id_pool:
            return self._id_pool.pop()
        self._id_next += 1
        return self._id_prefix + str(self._id_next)

    def free_id(self, x):
        """Free the given ID."""
        if x.startswith(self._id_prefix):
            self._id_pool.append(x)
