# easysh

an easy to execute shell in python

## Requirements

Python 3.3 + 


## Installation

```shell
pip install easysh
```

## Usage

```python
from easysh import Shell

output= Shell.exec('ls -l')
print(output)
```

asyncio

```python
from easysh import Shell

output= await Shell.aexec('ls -l',cwd='/var')
print(output)
```

Real-time output

```python
from easysh import Shell

with Shell.create('ls -l') as std:
    for line in std:
        print(line)
```

asyncio Real-time output

```python
from easysh import Shell

async with Shell.create('ls -l') as std:
    async for line in std:
        print(line)
``` 

execute shell command with timeout

```python
from easysh import Shell
from subprocess import TimeoutExpired

try:
    await Shell.aexec('python', timeout=3)
except TimeoutExpired as e:
    print(e)

``` 

handling error

```python
from easysh import Shell, ShellError

try:
    Shell.exec("unknown command")
except ShellError as e:
    print(e)

``` 

capturing the output and error streams

```python
from easysh import Shell

# capturing the output and error streams
with Shell.create("unknown command", raise_on_stderr=False) as std:
    output = std.read()
    print(output)
    print(std.has_errors)
``` 

