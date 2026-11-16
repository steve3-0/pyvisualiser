#!/usr/bin/env python
"""
 pyvisualiser project

Audio Ring Buffer
    - Thread-safe, Lock-Free Circular Ring Buffer for Real-Time Audio DSP.
    - Single-Producer Single-Consumer (SPSC) with zero-copy slice reads.
    - Intended for use with PyAudio callback threads and real-time render loops.

 baloothebear4
 v1.0 Nov 2026

"""

import numpy as np


class AudioRingBuffer:
    """
    Lock-free circular audio ring buffer backed by a contiguous NumPy int16 array.
    Uses mirrored buffer padding to guarantee contiguous slice reads across the boundary.
    """
    def __init__(self, capacity: int = 32768, max_chunk: int = 4096):
        self.capacity = int(capacity)
        self.max_chunk = int(max_chunk)

        # Mirrored buffer: capacity + max_chunk allows wrapping reads without stitching
        self._buffer = np.zeros(self.capacity + self.max_chunk, dtype=np.int16)
        
        self._write_idx = 0
        self._read_idx = 0
        self._total_written = 0
        self._total_read = 0

    @property
    def available_read(self) -> int:
        """Total unread samples currently available."""
        return self._total_written - self._total_read

    @property
    def available_write(self) -> int:
        """Remaining capacity before unread data is overwritten."""
        return self.capacity - self.available_read

    def write(self, data: np.ndarray | bytes) -> int:
        """
        Writes audio samples into the ring buffer (called by PyAudio capture thread).
        Never blocks. Gracefully overwrites the oldest data if full.
        """
        if isinstance(data, (bytes, bytearray)):
            samples = np.frombuffer(data, dtype=np.int16)
        else:
            samples = data

        num_samples = len(samples)
        if num_samples == 0:
            return 0

        w = self._write_idx
        cap = self.capacity

        # Check if write will exceed capacity and advance read pointer to prevent stale lag
        if num_samples > cap:
            # Buffer too small for chunk: keep only the newest samples
            samples = samples[-cap:]
            num_samples = cap

        if self.available_read + num_samples > cap:
            # Overwrite headroom: advance read index to drop oldest unread samples
            overflow = (self.available_read + num_samples) - cap
            self._total_read += overflow
            self._read_idx = (self._read_idx + overflow) % cap

        # Write samples into buffer
        space_to_end = cap - w
        if num_samples <= space_to_end:
            self._buffer[w:w + num_samples] = samples
            # Mirror to padding if writing in the lower boundary zone
            if w < self.max_chunk:
                overlap = min(num_samples, self.max_chunk - w)
                self._buffer[cap + w:cap + w + overlap] = samples[:overlap]
        else:
            # Wraps around the boundary
            self._buffer[w:cap] = samples[:space_to_end]
            remainder = num_samples - space_to_end
            self._buffer[0:remainder] = samples[space_to_end:]
            # Mirror the wrap chunk to the extended buffer area
            self._buffer[cap:cap + remainder] = samples[space_to_end:]

        self._write_idx = (w + num_samples) % cap
        self._total_written += num_samples
        return num_samples

    def read(self, count: int) -> np.ndarray | None:
        """
        Reads `count` sequential samples and advances the read pointer.
        Returns a zero-copy slice from the mirrored buffer, or None if insufficient samples.
        """
        if self.available_read < count:
            return None

        r = self._read_idx
        # Mirrored array ensures buffer[r:r+count] is always valid and contiguous
        result = self._buffer[r:r + count]

        self._read_idx = (r + count) % self.capacity
        self._total_read += count
        return result

    def read_latest(self, count: int) -> np.ndarray:
        """
        Retrieves the most recent `count` samples and advances the read pointer to the write head.
        Guarantees instant real-time synchronization without audio lag.
        """
        count = min(count, self.capacity)
        w = self._write_idx
        cap = self.capacity

        if w >= count:
            result = self._buffer[w - count:w]
        else:
            # Read from mirrored boundary
            start = cap + w - count
            result = self._buffer[start:start + count]

        # Sync read pointer to head
        self._read_idx = w
        self._total_read = self._total_written
        return result

    def clear(self):
        self._write_idx = 0
        self._read_idx = 0
        self._total_written = 0
        self._total_read = 0
        self._buffer.fill(0)