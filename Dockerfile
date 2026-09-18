FROM python:3.10-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    gcc \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Patch pyrogram/kurigram sync.py to fix "Future attached to a different loop"
# Only patches async_to_sync_wrap to use the running loop, keeps idle/compose intact
RUN python3 - <<'PYEOF'
import pyrogram, os, re

sync_path = os.path.join(os.path.dirname(pyrogram.__file__), 'sync.py')
with open(sync_path, 'r') as f:
    content = f.read()

# Replace the async_to_sync function with a version that detects the running loop at call time
old_func = '''def async_to_sync(obj, name):
    function = getattr(obj, name)
    main_loop = asyncio.get_event_loop()

    def async_to_sync_gen(agen, loop, is_main_thread):
        async def anext(agen):
            try:
                return await agen.__anext__(), False
            except StopAsyncIteration:
                return None, True

        while True:
            if is_main_thread:
                item, done = loop.run_until_complete(anext(agen))
            else:
                item, done = asyncio.run_coroutine_threadsafe(anext(agen), loop).result()

            if done:
                break

            yield item

    @functools.wraps(function)
    def async_to_sync_wrap(*args, **kwargs):
        coroutine = function(*args, **kwargs)

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if threading.current_thread() is threading.main_thread() or not main_loop.is_running():
            if loop.is_running():
                return coroutine
            else:
                if inspect.iscoroutine(coroutine):
                    return loop.run_until_complete(coroutine)

                if inspect.isasyncgen(coroutine):
                    return async_to_sync_gen(coroutine, loop, True)
        else:
            if inspect.iscoroutine(coroutine):
                if loop.is_running():
                    async def coro_wrapper():
                        return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coroutine, main_loop))

                    return coro_wrapper()
                else:
                    return asyncio.run_coroutine_threadsafe(coroutine, main_loop).result()

            if inspect.isasyncgen(coroutine):
                if loop.is_running():
                    return coroutine
                else:
                    return async_to_sync_gen(coroutine, main_loop, False)

    setattr(obj, name, async_to_sync_wrap)'''

new_func = '''def async_to_sync(obj, name):
    function = getattr(obj, name)

    def async_to_sync_gen(agen, loop):
        async def anext(agen):
            try:
                return await agen.__anext__(), False
            except StopAsyncIteration:
                return None, True

        while True:
            item, done = asyncio.run_coroutine_threadsafe(anext(agen), loop).result()
            if done:
                break
            yield item

    @functools.wraps(function)
    def async_to_sync_wrap(*args, **kwargs):
        coroutine = function(*args, **kwargs)

        # Always get the currently running loop
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop is not None and running_loop.is_running():
            # We are inside an async context — return coroutine directly so it can be awaited
            if inspect.iscoroutine(coroutine):
                return coroutine
            if inspect.isasyncgen(coroutine):
                return coroutine
        else:
            # No running loop — run synchronously
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
                return async_to_sync_gen(coroutine, loop)

    setattr(obj, name, async_to_sync_wrap)'''

if old_func in content:
    content = content.replace(old_func, new_func)
    with open(sync_path, 'w') as f:
        f.write(content)
    print(f"Successfully patched {sync_path}")
else:
    print("WARNING: Could not find target function to patch - sync.py may have changed")
    print("Current content snippet:")
    print(content[:500])
PYEOF

# Copy application code and start script
COPY . .
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port range (since the script finds available port)
EXPOSE 7860-8000

# Set the start script as entrypoint
ENTRYPOINT ["./start.sh"]