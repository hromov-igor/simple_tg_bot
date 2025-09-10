import glob
from collections import Counter
from os import path


def parse_stats_from_logs(pattern="bot.log*"):
    user_ids = set()
    cmd_counter = Counter()
    total_size = 0

    for fname in glob.glob(pattern):
        total_size += path.getsize(fname)
        try:
            with open(fname, "r", encoding="utf-8") as f:
                for line in f:
                    if "STATS user_id=" not in line:
                        continue
                    parts = line.split()
                    for part in parts:
                        if part.startswith("user_id="):
                            try:
                                user_ids.add(int(part.split("=", 1)[1]))
                            except (ValueError, IndexError):
                                pass
                        elif part.startswith("command="):
                            try:
                                cmd = part.split("=", 1)[1].lstrip("/")
                                if cmd:
                                    cmd_counter[cmd] += 1
                            except IndexError:
                                pass
        except (IOError, OSError):
            continue

    return user_ids, cmd_counter, total_size


def format_timedelta(td) -> str:
    total_seconds = int(td.total_seconds())
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}д")
    if hours or days:
        parts.append(f"{hours}ч")
    parts.append(f"{minutes}м")
    parts.append(f"{seconds}с")
    return " ".join(parts)
