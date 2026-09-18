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

# Patch pyrogram/kurigram sync.py to prevent thread-based handler wrapping
# This fixes "Future attached to a different loop" when using kurimod
RUN SYNC_PATH=$(python3 -c "import pyrogram, os; print(os.path.join(os.path.dirname(pyrogram.__file__), 'sync.py'))") && \
    python3 - <<'EOF'
import pyrogram, os

sync_path = os.path.join(os.path.dirname(pyrogram.__file__), 'sync.py')
new_content = '''import asyncio
import functools


def async_to_sync(obj, name):
    function = getattr(obj, name)

    @functools.wraps(function)
    def async_to_sync_wrap(*args, **kwargs):
        coroutine = function(*args, **kwargs)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(coroutine, loop)
            return future.result()
        return loop.run_until_complete(coroutine)

    setattr(obj, name, async_to_sync_wrap)


def wrap(source):
    for name in source.__dict__:
        method = getattr(source, name)
        if callable(method) and asyncio.iscoroutinefunction(method):
            async_to_sync(source, name)
'''
with open(sync_path, 'w') as f:
    f.write(new_content)
print(f"Patched {sync_path}")
EOF

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