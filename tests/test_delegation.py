"""Test suite for agent delegation system."""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Set

from agent.router import DelegationRouter, RoutePolicy, CLIDelegator
from agent.communication import AgentCommunicator, AgentMessage
from agent.agent import TaskProcessingAgent, AgentCapability

# ... rest of the file remains unchanged ... 