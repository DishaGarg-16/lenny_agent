import time
import asyncio
from typing import Dict, List
from fastapi import Request, HTTPException, status

class InMemoryRateLimiter:
    """Sliding-window in-memory IP rate limiter to protect API against DoS spamming."""
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests_map: Dict[str, List[float]] = {}

    def check_rate_limit(self, client_ip: str):
        now = time.time()
        timestamps = self.requests_map.get(client_ip, [])
        # Retain only timestamps within the active sliding window
        valid_timestamps = [t for t in timestamps if now - t < self.window_seconds]
        if len(valid_timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: Max {self.max_requests} requests per minute."
            )
        valid_timestamps.append(now)
        self.requests_map[client_ip] = valid_timestamps

# Concurrency semaphore limiting simultaneous local LLM inferences to prevent RAM/VRAM spikes
LLM_CONCURRENCY_SEMAPHORE = asyncio.Semaphore(5)
RATE_LIMITER = InMemoryRateLimiter(max_requests=30, window_seconds=60)
