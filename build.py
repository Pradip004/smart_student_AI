import os
import subprocess
import sys


def main():
    if os.environ.get("VERCEL_ENV") != "production":
        return
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL must be configured for production deployments.")
    subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        check=True,
    )


if __name__ == "__main__":
    main()
