import asyncio
from .shell_command import ShellCommand


class Shell:
    @staticmethod
    def exec(cmd: str,
             cwd: str = None,
             timeout=None,
             raise_error=True,
             encoding: str = None
             ) -> str or None:
        with Shell.create(
                cmd,
                cwd=cwd,
                timeout=timeout,
                raise_on_stderr=raise_error,
                encoding=encoding) as command:
            return command.read()

    # noinspection SpellCheckingInspection
    @staticmethod
    async def aexec(
            cmd: str,
            cwd: str = None,
            encoding: str = None,
            loop: asyncio.AbstractEventLoop = None,
            timeout: int = 60):
        async with ShellCommand(
                cmd=cmd,
                cwd=cwd,
                encoding=encoding,
                timeout=timeout,
                loop=loop) as command:
            return await command.read_async()

    @staticmethod
    def create(
            cmd: str,
            cwd: str = None,
            encoding: str = None,
            loop: asyncio.AbstractEventLoop = None,
            timeout: int = 60,
            raise_on_stderr: bool = True
    ):
        return ShellCommand(
            cmd=cmd,
            cwd=cwd,
            encoding=encoding,
            timeout=timeout,
            raise_on_stderr=raise_on_stderr,
            loop=loop)
