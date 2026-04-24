# llm/rate_limiter.py

import time
import threading
import random

class RateLimiter:
    def __init__(self, rpm: int):
        self.interval = 60.0 / rpm
        self.lock = threading.Lock()
        self.next_allowed_time = time.time()

    def wait(self):
        with self.lock:
            now = time.time()

            if now < self.next_allowed_time:
                sleep_time = self.next_allowed_time - now
                time.sleep(sleep_time + random.uniform(0, 0.3))

            # schedule next slot properly (prevents drift)
            self.next_allowed_time = max(now, self.next_allowed_time) + self.interval