import asyncio
import subprocess
from threading import Timer
from typing import Union, Optional

import chardet
from .shell_error import ShellError


class ShellCommand:
    def __init__(
            self,
            process: Union[asyncio.subprocess.Process, subprocess.Popen] = None,
            cmd: str = None,
            cwd: str = None,
            encoding: str = None,
            timeout: int = None,
            raise_on_stderr: bool = True,
            loop: asyncio.AbstractEventLoop = None):
        self._encoding = encoding
        self._process: Union[asyncio.subprocess.Process, subprocess.Popen] = process
        self._has_errors: bool = False
        self._timeout: int = timeout
        self._is_timeout: bool = False
        self._loop = loop or asyncio.get_event_loop()
        self._cmd = cmd
        self._cwd = cwd
        self._raise_on_stderr = raise_on_stderr
        self._timer: Optional[Timer] = None
        self._is_closing = False
        self._is_closed: bool = False
        self._is_iter: bool = False

    @property
    def has_errors(self):
        return self._has_errors

    @property
    def is_closed(self):
        return self._is_closed

    @property
    def is_timeout(self):
        return self._is_timeout

    def _timeout_callback(self):
        self._is_timeout = True
        self.close()

    def _async_timeout_callback(self):
        self._is_timeout = True
        self._process.stdout.feed_eof()
        self._process.stderr.feed_eof()
        self._process.kill()

    def _decode(self, value: Union[bytes, str]) -> str or None:
        if not value:
            return None
        if isinstance(value, str):
            return value
        if not self._encoding:
            self._encoding = chardet.detect(value).get('encoding')
        return value.decode(self._encoding).strip()

    def _create_process(self):
        if self._process:
            return
        self._process = subprocess.Popen(
            self._cmd,
            cwd=self._cwd,
            shell=True,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=-1)

    async def _create_async_subprocess(self):
        if self._process:
            return
        self._process = await asyncio.create_subprocess_shell(
            cmd=self._cmd,
            cwd=self._cwd,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

    def _read_std(self, stdout: bytes, stderr: bytes):
        if not stdout and not stderr:
            return
        if stdout and not stderr:
            return self._decode(stdout)
        self._has_errors = True
        decoded_error = self._decode(stderr)
        if self._raise_on_stderr:
            raise ShellError(decoded_error)
        if stdout:
            return f'{self._decode(stdout)}\n{decoded_error}'
        return decoded_error

    def close(self):
        if not self._process or self._is_closing or self._is_closed:
            return
        self._is_closing = True
        self._timer and self._timer.cancel()
        if self._is_iter:
            self._process.kill()
        self._process.wait()
        self._is_closed = True

    # noinspection SpellCheckingInspection
    async def aclose(self):
        if not self._process \
                or self._is_closing \
                or self._is_closed:
            return
        self._is_closing = True
        # fix ValueError: I/O operation on closed file when using asyncio with subprocess
        # noinspection PyUnresolvedReferences,PyProtectedMember
        self._process._transport.close()
        # noinspection PyUnresolvedReferences,PyProtectedMember
        self._process._transport.close()
        if self._is_iter:
            self._process.kill()
        await self._process.wait()
        self._is_closed = True

    def read(self) -> str or None:
        self._create_process()
        stdout, stderr = self._process.communicate(timeout=self._timeout)
        return self._read_std(stdout, stderr)

    async def read_async(self) -> str or None:
        self._set_timeout_handler()
        await self._create_async_subprocess()
        stdout, stderr = await self._process.communicate()
        self._timeout_handler and self._timeout_handler.cancel()
        if self._is_timeout:
            raise subprocess.TimeoutExpired(self._cmd, self._timeout)
        return self._read_std(stdout, stderr)

    def __iter__(self):
        self._is_iter = True
        if self._timeout:
            self._timer = Timer(self._timeout, self._timeout_callback)
            self._timer.start()
        return self

    def _set_timeout_handler(self):
        if self._timeout:
            self._timeout_handler = self._loop.call_later(self._timeout, self._async_timeout_callback)

    def __aiter__(self):
        self._is_iter = True
        self._set_timeout_handler()
        return self

    def __next__(self):
        if self._is_closing:
            raise StopIteration
        self._create_process()
        value = self._process.stdout.readline()
        if not value:
            value = self._process.stderr.readline()
            if value:
                self._has_errors = True
                if self._raise_on_stderr:
                    raise ShellError(self._decode(value))
        if not value or self._is_timeout:
            self.close()
            if self._is_timeout:
                raise subprocess.TimeoutExpired(cmd=self._cmd, timeout=self._timeout)
            raise StopIteration
        return self._decode(value)

    async def __anext__(self):
        if self._is_closing:
            raise StopAsyncIteration
        await self._create_async_subprocess()
        value = await self._process.stdout.readline()
        if self._process.stdout.at_eof():
            value = await self._process.stderr.readline()
            if value:
                self._has_errors = True
                if self._raise_on_stderr:
                    raise ShellError(self._decode(value))
            if self._process.stderr.at_eof():
                self._timeout_handler and self._timeout_handler.cancel()
                if self._is_timeout:
                    raise subprocess.TimeoutExpired(cmd=self._cmd, timeout=self._timeout)
                raise StopAsyncIteration
        return self._decode(value)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
