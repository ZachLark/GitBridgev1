"""
Event processor implementation for GitBridge.
Handles event payload optimization and processing.
"""

from dataclasses import dataclass
from typing import Dict, Any, AsyncGenerator
import asyncio
from contextlib import asynccontextmanager

@dataclass
class EventPayload:
    """Event payload data structure."""
    id: str
    type: str
    payload: dict

async def optimize_payload(event: EventPayload) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Optimizes event payload processing through async generator pattern.
    Compresses parse/assign/mutate operations.
    """
    try:
        # Process payload in chunks to optimize memory
        async for item in _process_payload_chunks(event.payload):
            # Apply optimizations
            if isinstance(item, dict):
                item = await _optimize_dict(item)
            yield item
    except Exception as e:
        # Log error but don't break processing
        print(f"Error optimizing payload {event.id}: {str(e)}")
        yield event.payload

async def _process_payload_chunks(payload: dict) -> AsyncGenerator[Dict[str, Any], None]:
    """Process payload in chunks for memory optimization."""
    chunk_size = 1024  # 1KB chunks
    items = list(payload.items())
    
    for i in range(0, len(items), chunk_size):
        chunk = dict(items[i:i + chunk_size])
        yield chunk
        await asyncio.sleep(0)  # Yield control

async def _optimize_dict(data: dict) -> dict:
    """Optimize dictionary structure."""
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    # Compress nested structures
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = await _optimize_dict(value)
    
    return data 