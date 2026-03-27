#!/usr/bin/env python3
"""
One-time migration: fix posts that have NULL or empty timestamps.

Run once on the server after deploying the updated app.py:

    python scripts/fix_null_timestamps.py

By default it targets posts.db in the current directory.
Pass the path as an argument to target a different file:

    python scripts/fix_null_timestamps.py /var/data/posts.db

The script sets a sentinel timestamp of '1970-01-01T00:00:00' so that these
posts appear in the calendar (Jan 1970) rather than being silently dropped.
You can then edit them via the Streamlit UI or the PATCH /api/posts/{id}
endpoint to set the correct date.
"""

import sqlite3
import sys

SENTINEL_TS = "1970-01-01T00:00:00"


def fix_null_timestamps(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Count affected rows
    c.execute(
        "SELECT COUNT(*) FROM post_history WHERE timestamp IS NULL OR timestamp = ''"
    )
    count = c.fetchone()[0]

    if count == 0:
        print(f"[OK] No NULL/empty timestamps found in {db_path}.")
        conn.close()
        return

    print(f"[INFO] Found {count} post(s) with NULL or empty timestamp in {db_path}.")
    print(f"[INFO] Setting sentinel timestamp: {SENTINEL_TS}")

    c.execute(
        "UPDATE post_history SET timestamp = ? WHERE timestamp IS NULL OR timestamp = ''",
        (SENTINEL_TS,),
    )
    conn.commit()
    print(f"[OK] Updated {c.rowcount} row(s). These posts now appear in the January 1970 calendar cell.")
    print("     Use PATCH /api/posts/{id} or the Streamlit UI to set the correct date.")
    conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "posts.db"
    fix_null_timestamps(db_path)
