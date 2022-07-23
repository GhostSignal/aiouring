from asyncio.events import BaseDefaultEventLoopPolicy
from asyncio.proactor_events import BaseProactorEventLoop
from ._core import UringProactor


class UringProactorEventLoop(BaseProactorEventLoop):
    """Linux version of proactor event loop using io_uring."""

    def __init__(self, proactor=None):
        super().__init__(proactor or UringProactor(4096, 0))


class UringEventLoopPolicy(BaseDefaultEventLoopPolicy):
    _loop_factory = UringProactorEventLoop


del BaseDefaultEventLoopPolicy
del BaseProactorEventLoop
