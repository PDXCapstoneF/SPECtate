from threading import Thread
from queue import Queue, Empty


class stream:
    def __init__(self, s):
        """
        s: the stream to read from.
        """

        self._stream = s
        self._queue = Queue()
        self._active = True


        self._t = Thread(target = self._read, args = (self._stream, self, self._queue))
        self._t.daemon = True
        self._t.start()

    @staticmethod
    def _read(st, parent, queue):
        """
        Collect lines from 'stream' and put them in 'queue'.
        """

        while parent._active:
            line = st.readline()
            if line:
                queue.put(line)
            else:
                parent._active = False

    def readline(self):
        if self._active:
            try:
                return self._queue.get_nowait()
            except Empty:
                return ''
        return ''

    def close(self):
        if(self._active):
            self._active = False