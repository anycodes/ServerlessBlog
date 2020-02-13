# coding: utf8

import time
import sys
import math
import struct

try:
    IS_TTY = sys.stdout.isatty()
except AttributeError:
    IS_TTY = False


def _console_width(default=80):
    if sys.platform.startswith('win'):
        width, height = _console_size_win()
    else:
        width, height = _console_size_unix()
    return width or default


def _console_size_unix():
    import termios
    import fcntl

    if not IS_TTY:
        return 0, 0

    s = struct.pack("HHHH", 0, 0, 0, 0)
    fd_stdout = sys.stdout.fileno()
    size = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, s)
    height, width = struct.unpack("HHHH", size)[:2]
    return width, height


def _console_size_win():
    # http://code.activestate.com/recipes/440694/
    from ctypes import windll, create_string_buffer

    STDIN, STDOUT, STDERR = -10, -11, -12

    h = windll.kernel32.GetStdHandle(STDERR)
    csbi = create_string_buffer(22)
    res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)

    if not res:
        left, top, right, bottom = struct.unpack("hhhhHhhhhhh", csbi.raw)[5:9]
        return right - left + 1, bottom - top + 1

    return 0, 0


class Progress(object):
    def __init__(self, label='', unit='', interval=0.4, scale=1, bar=10, bar_chars='# ',
                 spinner_chars='\\|/-'):
        self.label = label
        self.unit = unit
        self.interval = interval
        self.scale = scale
        self.bar = bar
        self.bar_chars = bar_chars
        self.spinner_chars = spinner_chars

        self.tps = 0
        now = time.time()

        self._done = 0
        self._items = None
        self.started = now
        self.last_shown = 0
        self.last_change = now

    def show(self, force=False):
        now = time.time()

        if not force and now - self.last_shown < self.interval:
            return

        self.last_shown = now

        if self._items:
            if self.tps == 0:
                eta = self.ftime(-1)
            else:
                elapsed = now - self.last_change
                eta = self.ftime((self._items - self._done) / self.tps - elapsed)

            bar = self.fbar()
            done = self.fvalue(self._done)
            items = self.fvalue(self._items)

            if len(done) < len(items):
                done = ' ' * (len(items) - len(done)) + done

            line = '[%s] %s/%s %s (ETA %s)' % (bar, done, items, self.unit, eta)
        else:
            line = '[%s] %s %s (ETC %s)' % (
            self.fspinner(), self.fvalue(self._done), self.unit, self.ftime(now - self.started))

        self.print_lr(self.label, line)

    def ftime(self, delta):
        if delta > 60 * 60 * 99 or delta < 0:
            return '**:**:**'
        sec = delta % 60
        mns = (delta // 60) % 60
        hrs = delta // 60 // 60
        return '%02i:%02i:%02i' % (hrs, mns, sec)

    def fvalue(self, value, maxdigits=4):
        for fac, prefix in enumerate([''] + list(self.scale_prefix)):
            test = float(value) / (self.scale ** fac)
            if test < 1 or math.log10(test) + 1 < maxdigits:
                if int(test * 10 ** maxdigits) % 10 ** maxdigits:
                    return ('%f' % test)[:maxdigits] + prefix
                else:
                    return ('%i' % test) + prefix
        return '*' * maxdigits

    def fvalue(self, value, mindigits=4):
        return str(value // self.scale)

    def fbar(self, value=None):
        if value is None:
            value = float(self._done) / self._items if self._items else 0.0
        on = int(value * self.bar)
        off = self.bar - on
        return '%s%s' % (self.bar_chars[0] * on, self.bar_chars[1] * off)

    def fspinner(self, i=None):
        if i is None:
            i = (time.time() - self.started) / self.interval
        return '%s' % self.spinner_chars[int(i) % len(self.spinner_chars)]

    def print_lr(self, label, line):
        cols = _console_width()
        ws = (cols - len(self.label) - len(line))
        if ws < 0:
            label = label[:ws - 4] + '... '
            ws = 0
        self._print('\r' + label + ' ' * ws + line)

    def println(self, line):
        line = str(line).rstrip()
        cols = _console_width()
        if len(line) < cols:
            line += ' ' * (cols - len(line))
        self._print(line + '\n')

    def wrapiter(self, iterable):
        try:
            self.items = len(iterable)
        except TypeError:
            pass

        for item in iterable:
            self.done += 1
            yield item

    def map(self, func, iterator):
        return map(func, self.wrapiter(iterator))

    def reset(self):
        now = time.time()
        self.items = None
        self.done = 0
        self.started = now

    def set_items(self, n):
        self._items = n
        self.show(force=True)

    def get_items(self):
        return self._items or 0

    items = property(get_items, set_items)
    del set_items, get_items

    def set_done(self, n):
        self._done = n
        self.last_change = time.time()
        self.tps = float(self._done) / (self.last_change - self.started)
        if self._items is not None and self._done > self._items:
            self._items = self._done
        self.show()

    def get_done(self):
        return self._done

    done = property(get_done, set_done)
    del set_done, get_done

    def __enter__(self):
        self.print_lr(self.label, "[...]")
        return self

    def __exit__(self, *a):
        self.show(force=True)

        now = time.time()
        delta = now - self.started

        if a[1] and isinstance(a[1], KeyboardInterrupt):
            line = '[ABORT]'
        elif a[1]:
            line = '[%r]' % a[1]
        elif self._done:
            line = '[DONE] %s %s (%s)' % (
                self.fvalue(self._done), self.unit, self.ftime(now-self.started)
            )
        else:
            line = '[DONE]'

        self.print_lr(self.label, line)
        self._print('\n')

    def _print(self, str):
        if IS_TTY:
            sys.stderr.write(str)
            sys.stderr.flush()


if __name__ == '__main__':
    with Progress('Test %r' % sys.argv, 'MB') as p:
        #p.items = int(sys.argv[1])
        while p.done < int(sys.argv[1]):
            p.done += 1
            time.sleep(float(sys.argv[2]) / int(sys.argv[1]))

