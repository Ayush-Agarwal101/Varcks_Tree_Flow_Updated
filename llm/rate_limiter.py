# llm/rate_limiter.py

import time
import random
import threading

class TokenBucket:
    def __init__(self, rate: int, capacity: int):
        self.rate_per_sec = rate / 60.0     # tokens added per minute
        self.capacity = capacity            # max burst size
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def wait(self):
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_refill

                # refill tokens
                refill = elapsed * self.rate_per_sec
                self.tokens = min(self.capacity, self.tokens + refill)
                self.last_refill = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

                # need to wait
                needed = 1 - self.tokens
                wait_time = needed / self.rate_per_sec

            time.sleep(wait_time + random.uniform(0.1, 0.3))