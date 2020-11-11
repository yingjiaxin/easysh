from unittest.mock import MagicMock

import pytest
from subprocess import TimeoutExpired
from easysh import Shell, ShellError, ShellCommand
import socket


def test_create():
    shell = Shell.create('hostname')
    assert shell.read() == socket.gethostname()


def test_exec():
    hostname = Shell.exec('hostname')
    assert hostname == socket.gethostname()


# noinspection SpellCheckingInspection
@pytest.mark.asyncio
async def test_aexec():
    assert await Shell.aexec('hostname') == socket.gethostname()


@pytest.mark.asyncio
async def test_read_async():
    async with Shell.create('hostname') as command:
        hostname = await command.read_async()
        assert hostname == socket.gethostname()
        assert command.is_timeout == False


def test_read_timeout():
    with pytest.raises(TimeoutExpired):
        with Shell.create('python task.py', timeout=1) as command:
            print(command.read())


def test_iter_timeout():
    with pytest.raises(TimeoutExpired):
        with Shell.create('python task.py', timeout=1) as command:
            for line in command:
                print(line)
            # duplicate close
            command.close()
        assert command.is_timeout == True


def test_iter_break():
    with Shell.create('python task.py', timeout=1) as std:
        for output in std:
            print(output)
            std.close()


@pytest.mark.asyncio
async def test_async_iter():
    async with Shell.create('python task.py', raise_on_stderr=False) as command:
        async for line in command:
            print(line)
        # duplicate close
        await command.aclose()
        assert command.has_errors == True
        assert command.is_closed == True


@pytest.mark.asyncio
async def test_async_iter_break():
    async with Shell.create('python task.py', raise_on_stderr=False) as std:
        async for line in std:
            print(line)
            await std.aclose()


def test_command_error():
    with Shell.create('foo', raise_on_stderr=False) as command:
        for line in command:
            print(line)
    assert command.is_closed == True
    assert command.has_errors == True


def test_raise_on_stderr():
    with pytest.raises(ShellError):
        with Shell.create('foo', raise_on_stderr=True) as command:
            for line in command:
                print(line)


@pytest.mark.asyncio
async def test_raise_on_stderr_async():
    with pytest.raises(ShellError):
        async with Shell.create('foo', raise_on_stderr=True) as command:
            async for line in command:
                print(line)


@pytest.mark.asyncio
async def test_timeout_async():
    with pytest.raises(TimeoutExpired) as e:
        async with Shell.create('python', timeout=1) as command:
            async for line in command:
                print(line)
        assert command.is_timeout == True


# noinspection SpellCheckingInspection
@pytest.mark.asyncio
async def test_timeout_aexec():
    with pytest.raises(TimeoutExpired):
        output = await Shell.aexec('python', timeout=1)
        print(output)


def test__decode():
    cmd = ShellCommand()
    assert cmd._decode(None) is None
    assert cmd._decode('foo') == 'foo'
    assert cmd._decode(b'foo') == 'foo'
    # assert cmd._decode(b'\xe4\xb8\xad\xe6\x96\x87') == '中文'


@pytest.mark.asyncio
async def test__read_std():
    cmd = ShellCommand(raise_on_stderr=False)
    cmd._decode = MagicMock(return_value='foo')
    assert cmd._read_std(b'', b'') is None
    assert cmd._read_std(b'', b'foo') == 'foo'
    assert cmd._read_std(b'foo', b'') == 'foo'
    assert cmd._read_std(b'foo', b'foo') == 'foo\nfoo'

    cmd_raise = ShellCommand()
    with pytest.raises(ShellError):
        cmd._decode = MagicMock(return_value='foo')
        cmd_raise._read_std(b'', b'foo')


