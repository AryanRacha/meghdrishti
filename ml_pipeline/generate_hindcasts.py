"""
Overnight Pangu-Weather Hindcast Generator (Bulletproof Edition)
- Removed 2020 (no matching GFS on NOAA AWS)
- Retries failed days up to 3 times before skipping
- Never aborts the entire pool for a single failure
- Logs all failures to a file for morning review
"""
import os
import subprocess
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30


def run_ai_model(date_str: str, output_file: str) -> tuple[bool, str]:
    if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
        return True, f"Skipping {date_str}, already generated."

    # Remove any corrupt/empty leftover files from previous failed runs
    if os.path.exists(output_file):
        os.remove(output_file)

    cmd = [
        "ai-models",
        "--date", date_str,
        "--time", "0000",
        "--lead-time", "24",
        "--input", "cds",
        "--path", output_file,
        "panguweather"
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600)
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                return True, f"Generated {output_file}"
            else:
                raise RuntimeError("Output file missing or empty after inference")
        except Exception as e:
            error_msg = e.stderr.decode('utf-8', errors='replace') if hasattr(e, 'stderr') and e.stderr else str(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                return False, f"FAILED {date_str} after {MAX_RETRIES} attempts: {error_msg[-200:]}"

    return False, f"FAILED {date_str}: unknown error"


def generate_pangu_weather_hindcasts():
    # 2020 removed — NOAA AWS has no GFS data for 2020
    date_ranges = [
        ("2021-06-01", "2021-09-30"),
        ("2022-06-01", "2022-09-30"),
        ("2023-06-01", "2023-09-30"),
        ("2021-12-01", "2022-02-28"),
        ("2022-12-01", "2023-02-28"),
    ]

    os.makedirs('data/raw/pangu', exist_ok=True)

    tasks: list[tuple[str, str]] = []
    for start_date, end_date in date_ranges:
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        while current <= end:
            ds = current.strftime("%Y%m%d")
            tasks.append((ds, f"data/raw/pangu/pangu_{ds}.grib"))
            current += timedelta(days=1)

    print(f"Queueing {len(tasks)} hindcast generations utilizing 3 parallel workers...")

    failures: list[str] = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_ai_model, d, f): d for d, f in tasks}

        for future in tqdm(as_completed(futures), total=len(futures), desc="Generating Hindcasts"):
            success, message = future.result()
            if not success:
                failures.append(message)

    # Write failure log for morning review
    if failures:
        with open("hindcast_failures.log", "w") as f:
            f.write("\n".join(failures))
        print(f"\n{len(failures)} days failed. See hindcast_failures.log for details.")
    else:
        print("\nAll hindcasts generated successfully!")


if __name__ == "__main__":
    generate_pangu_weather_hindcasts()
