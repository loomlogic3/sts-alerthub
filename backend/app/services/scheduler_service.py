import os
import threading
import time


def start_scheduler(job_function):
    enabled = (
        os.getenv("AUTO_MONITOR_ENABLED", "false")
        .lower()
        .strip()
        == "true"
    )

    if not enabled:
        print("Scheduler disabled.")
        return

    interval = int(
        os.getenv(
            "AUTO_MONITOR_INTERVAL_SECONDS",
            "300",
        )
    )

    def scheduler_loop():
        print(
            f"Scheduler started "
            f"(interval={interval}s)"
        )

        try:
            job_function()
        except Exception as exc:
            print(
                f"Scheduler startup run failed: {exc}"
            )

        while True:
            time.sleep(interval)

            try:
                job_function()
            except Exception as exc:
                print(
                    f"Scheduler run failed: {exc}"
                )

    thread = threading.Thread(
        target=scheduler_loop,
        daemon=True,
    )

    thread.start()
