import concurrent.futures
import json
import threading
import time

# Import your function
from arxiv_metadata import get_full_metadata

ARXIV_ID = "1706.03762"

TOTAL_REQUESTS = 1000
REQUESTS_PER_SECOND = 1000 / 60 

lock = threading.Lock()

passed = 0
failed = 0
latencies = []


def worker(i):
    global passed, failed

    start = time.perf_counter()

    try:
        result = json.loads(get_full_metadata(ARXIV_ID))

        elapsed = time.perf_counter() - start

        with lock:
            latencies.append(elapsed)

            if "error" not in result:
                passed += 1
            else:
                failed += 1

    except Exception:
        with lock:
            failed += 1


def main():
    start_time = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = []

        for i in range(TOTAL_REQUESTS):
            futures.append(executor.submit(worker, i))
            time.sleep(1 / REQUESTS_PER_SECOND)

        concurrent.futures.wait(futures)

    total_time = time.perf_counter() - start_time

    print("=" * 50)
    print(f"Total Requests : {TOTAL_REQUESTS}")
    print(f"Passed         : {passed}")
    print(f"Failed         : {failed}")
    print(f"Success Rate   : {passed / TOTAL_REQUESTS * 100:.2f}%")
    print(f"Duration       : {total_time:.2f} sec")

    if latencies:
        print(f"Average Latency: {sum(latencies)/len(latencies):.3f} sec")
        print(f"Min Latency    : {min(latencies):.3f} sec")
        print(f"Max Latency    : {max(latencies):.3f} sec")


if __name__ == "__main__":
    main()
