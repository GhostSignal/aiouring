# distutils:language=c++
# cython:language_level=3

import asyncio
import socket

cdef extern from "UringWraper.hpp":
    cdef struct io_uring_cqe:
        long long user_data
        signed res
        unsigned flags

    cdef cppclass UringWraper:
        signed queue_init(unsigned entries, unsigned flags)

        void wait_cqe(io_uring_cqe ** cqe_ptr, double timeout_sec)
        void peek_cqe(io_uring_cqe ** cqe_ptr)
        void cqe_seen(io_uring_cqe * cqe)

        long long do_read(signed fd, char * buf, unsigned nbytes, unsigned long long offset)
        long long do_write(signed fd, char * buf, unsigned nbytes, unsigned long long offset)
        long long do_poll_add(signed fd, unsigned poll_mask)
        long long do_timeout(char * buf_16bytes, double timeout_sec)
        long long do_cancel(long long user_data, signed flags)

cdef class UringProactor:
    cdef UringWraper _ring
    cdef object _loop
    cdef dict _cache

    def __init__(self, entries: int, flags: int):
        assert self._ring.queue_init(entries, flags) == 0
        self._cache: dict = dict()

    def set_loop(self, loop: asyncio.BaseEventLoop):
        def hijack_call_at(when, callback, *args, context=None):
            timer = asyncio.TimerHandle(when, callback, args, loop, context)
            if timer._source_traceback:
                del timer._source_traceback[-1]
            loop._proactor._schedule_timer(timer)
            return timer
        self._loop = loop
        loop.call_at = hijack_call_at

    def _schedule_timer(self, timer: asyncio.TimerHandle):
        timeout_sec: float = timer.when() - self._loop.time()
        if timeout_sec <= 0:
            self._loop._ready.append(timer)
            return
        buf = bytearray(16)
        cdef long long key = self._ring.do_timeout(buf, timeout_sec)

        def finish_timeout(res: int):
            self._loop._ready.append(timer)
        self._register(key, buf, finish_timeout)

    def connect(self, conn: socket.socket, address: tuple):
        conn.connect_ex(address)
        cdef long long key = self._ring.do_poll_add(
            conn.fileno(),
            0xffffffff
        )

        def finish_connect(res: int):
            conn.getpeername()
        return self._register(key, None, finish_connect)

    def accept(self, conn: socket.socket):
        cdef long long key = self._ring.do_poll_add(
            conn.fileno(),
            0xffffffff
        )

        def finish_accept(res: int):
            return conn.accept()
        return self._register(key, None, finish_accept)

    def recv_into(self, conn: socket.socket, buf: bytearray):
        cdef long long key = self._ring.do_read(conn.fileno(), buf, len(buf), 0)

        def finish_recv(res: int):
            if res < 0:
                raise OSError(res)
            return res
        return self._register(key, buf, finish_recv)

    def send(self, conn: socket.socket, buf: bytes):
        cdef long long key = self._ring.do_write(conn.fileno(), buf, len(buf), 0)

        def finish_send(res: int):
            if res < 0:
                raise OSError(res)
            return res
        return self._register(key, buf, finish_send)

    cdef object _register(self, long long key, object obj, object callback):
        fut = asyncio.Future(loop=self._loop)
        self._cache[key] = (fut, obj, callback)

        def cancel_ring_event(*args):
            if key in self._cache:
                self._ring.do_cancel(key, 0)
                self._cache.pop(key)
        fut.add_done_callback(cancel_ring_event)
        return fut

    cdef void _poll(self, double timeout):
        cdef io_uring_cqe * cqe
        self._ring.wait_cqe( & cqe, timeout)
        while ( < long long > cqe):
            try:
                fut, _, callback = self._cache.pop(cqe[0].user_data)
            except KeyError:
                self._ring.cqe_seen(cqe)
                self._ring.peek_cqe( & cqe)
                continue

            if not fut.done():
                try:
                    value = callback(cqe[0].res)
                except OSError as exc:
                    fut.set_exception(exc)
                else:
                    fut.set_result(value)

            self._ring.cqe_seen(cqe)
            self._ring.peek_cqe( & cqe)

    def select(self, timeout: float = None):
        self._poll(timeout or 0)
        return []

    def close(self):
        for fut, _, _ in self._cache.values():
            fut.cancel()

    def __del__(self):
        self.close()
