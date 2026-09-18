"""
Patch pyrogram sync.py at runtime before any import.
Run this before importing pyrogram.
"""
import ast
import os
import sys
import pyrogram

sync_path = os.path.join(os.path.dirname(pyrogram.__file__), "sync.py")

NEW_ASYNC_TO_SYNC = '''
def async_to_sync(obj, name):
    function = getattr(obj, name)

    @functools.wraps(function)
    def async_to_sync_wrap(*args, **kwargs):
        coroutine = function(*args, **kwargs)

        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop is not None:
            # Inside async context — return coroutine/asyncgen directly to be awaited
            return coroutine
        else:
            # Outside async context — run synchronously
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if inspect.iscoroutine(coroutine):
                return loop.run_until_complete(coroutine)
            if inspect.isasyncgen(coroutine):
                # For async generators, collect all items
                async def collect():
                    results = []
                    async for item in coroutine:
                        results.append(item)
                    return results
                return loop.run_until_complete(collect())

    setattr(obj, name, async_to_sync_wrap)
'''

with open(sync_path, "r") as f:
    content = f.read()

# Find and replace the async_to_sync function
import re

# Replace the entire async_to_sync function definition
pattern = r'def async_to_sync\(obj, name\):.*?(?=\ndef wrap\(source\))'
replacement = NEW_ASYNC_TO_SYNC.strip() + "\n\n"

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    with open(sync_path, "w") as f:
        f.write(new_content)
    print(f"[patch_sync] Successfully patched {sync_path}")
else:
    print(f"[patch_sync] WARNING: Pattern not matched, sync.py unchanged")
