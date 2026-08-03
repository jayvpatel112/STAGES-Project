"""
Create a tiny aggregated MaStR SQLite database for the STAGES project.

This preserves the exact national, state, technology, and storage-category
statistics used by storage.py, while avoiding the 10+ GB source database.

Run once on the computer that has the full open-mastr.db.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path


DEFAULT_SOURCE = Path.home() / ".open-MaStR" / "data" / "sqlite" / "open-mastr.db"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "mastr_storage_aggregated.db"


def create_database(source: Path, output: Path) -> None:
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(f"Source database not found: {source}")

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    started = time.perf_counter()
    con = sqlite3.connect(output)

    try:
        con.execute("PRAGMA journal_mode = WAL")
        con.execute("PRAGMA synchronous = NORMAL")
        con.execute("ATTACH DATABASE ? AS full_db", (str(source),))

        # A deduplicated base view keeps one record per MaStR number.
        # It contains only operational batteries with positive capacity.
        con.execute(
            """
            CREATE TEMP VIEW battery_base AS
            SELECT DISTINCT
                su.MastrNummer,
                su.NutzbareSpeicherkapazitaet,
                se.Bundesland,
                se.Ort,
                se.Technologie,
                se.Batterietechnologie
            FROM full_db.storage_units AS su
            LEFT JOIN full_db.storage_extended AS se
                ON su.MastrNummer = se.SpeMastrNummer
            WHERE su.AnlageBetriebsstatus = 'In Betrieb'
              AND se.Technologie = 'Batterie'
              AND su.NutzbareSpeicherkapazitaet IS NOT NULL
              AND su.NutzbareSpeicherkapazitaet > 0
            """
        )

        print("Creating battery_summary...")
        con.execute(
            """
            CREATE TABLE battery_summary AS
            SELECT
                COUNT(MastrNummer) AS Total_Systems,
                SUM(NutzbareSpeicherkapazitaet) / 1000000.0
                    AS Total_Capacity_GWh
            FROM battery_base
            """
        )

        print("Creating battery_by_state...")
        con.execute(
            """
            CREATE TABLE battery_by_state AS
            SELECT
                Bundesland,
                COUNT(MastrNummer) AS Total_Systems,
                SUM(NutzbareSpeicherkapazitaet) / 1000000.0
                    AS Total_Capacity_GWh
            FROM battery_base
            WHERE Bundesland IS NOT NULL
            GROUP BY Bundesland
            ORDER BY Total_Capacity_GWh DESC
            """
        )

        print("Creating battery_by_technology...")
        con.execute(
            """
            CREATE TABLE battery_by_technology AS
            SELECT
                Batterietechnologie,
                Technologie,
                COUNT(MastrNummer) AS Total_Systems,
                SUM(NutzbareSpeicherkapazitaet) / 1000000.0
                    AS Total_GWh
            FROM battery_base
            GROUP BY Batterietechnologie, Technologie
            ORDER BY Total_GWh DESC
            """
        )

        print("Creating battery_by_category...")
        con.execute(
            """
            CREATE TABLE battery_by_category AS
            WITH categorized AS (
                SELECT
                    MastrNummer,
                    NutzbareSpeicherkapazitaet,
                    CASE
                        WHEN NutzbareSpeicherkapazitaet <= 30
                            THEN 'Home Storage'
                        WHEN NutzbareSpeicherkapazitaet <= 1000
                            THEN 'Commercial Storage'
                        ELSE 'Large Scale Storage'
                    END AS Category
                FROM battery_base
            ),
            grouped AS (
                SELECT
                    Category,
                    COUNT(MastrNummer) AS Total_Systems,
                    SUM(NutzbareSpeicherkapazitaet) / 1000000.0
                        AS Total_GWh
                FROM categorized
                GROUP BY Category
            )
            SELECT
                Category,
                Total_Systems,
                Total_GWh,
                Total_GWh * 100.0 / SUM(Total_GWh) OVER () AS Share_percent
            FROM grouped
            ORDER BY Total_GWh DESC
            """
        )

        # Optional: preserve a small exact table of the largest installations
        # for inspection/demo purposes.
        print("Creating top_battery_locations...")
        con.execute(
            """
            CREATE TABLE top_battery_locations AS
            SELECT
                MastrNummer,
                Bundesland,
                Ort,
                Technologie,
                Batterietechnologie,
                NutzbareSpeicherkapazitaet
            FROM battery_base
            ORDER BY NutzbareSpeicherkapazitaet DESC
            LIMIT 500
            """
        )

        con.commit()
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        con.execute("VACUUM")

        size_kb = output.stat().st_size / 1024
        elapsed = time.perf_counter() - started

        print("\nDone.")
        print(f"Output: {output}")
        print(f"File size: {size_kb:.1f} KB")
        print(f"Elapsed time: {elapsed / 60:.1f} minutes")

        for table in (
            "battery_summary",
            "battery_by_state",
            "battery_by_technology",
            "battery_by_category",
            "top_battery_locations",
        ):
            count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            print(f"{table}: {count:,} rows")

    finally:
        con.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        create_database(args.source, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
