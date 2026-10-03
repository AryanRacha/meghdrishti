"""
Overnight GFS Bulk Downloader (Bulletproof Edition)
- Only targets 2021+ (NOAA AWS has no 2020 data)
- Retries failed downloads up to 3 times
- Never aborts the entire pool for a single failure
- Logs all failures to a file for morning review
"""
import os
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from data_fetchers.gfs_fetcher import GFSFetcher

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

def download_with_retry(fetcher, date_str: str, cycle: str, forecast_hour: int) -> tuple[bool, str]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = fetcher.fetch_historical_forecast(date_str, cycle, forecast_hour)
            if result is not None:
                return True, f"Successfully downloaded {date_str}"
            else:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    return False, f"FAILED {date_str} after {MAX_RETRIES} attempts (Not Found/404)"
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                return False, f"FAILED {date_str} after {MAX_RETRIES} attempts: {str(e)}"
    
    return False, f"FAILED {date_str}: unknown error"

def download_all_gfs():
    # 2020 removed — NOAA AWS has no GFS data for 2020
    date_ranges = [
        ("2021-06-01", "2021-09-30"),
        ("2022-06-01", "2022-09-30"),
        ("2023-06-01", "2023-09-30"),
        ("2021-12-01", "2022-02-28"),
        ("2022-12-01", "2023-02-28"),
    ]

    fetcher = GFSFetcher(output_dir="data/raw/gfs")

    tasks: list[str] = []
    for start_date, end_date in date_ranges:
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        while current <= end:
            tasks.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)

    print(f"Queueing {len(tasks)} GFS downloads utilizing 6 parallel workers (NOAA AWS)...")

    failures: list[str] = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(download_with_retry, fetcher, d, "00", 24): d
            for d in tasks
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading GFS"):
            success, message = future.result()
            if not success:
                failures.append(message)

    # Write failure log for morning review
    if failures:
        with open("gfs_failures.log", "w") as f:
            f.write("\n".join(failures))
        print(f"\n{len(failures)} days failed. See gfs_failures.log for details.")
    else:
        print("\nAll GFS downloads completed successfully!")


if __name__ == "__main__":
    download_all_gfs()
