from __future__ import annotations

import asyncio

from telegram_bot.runner import run_bot


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
