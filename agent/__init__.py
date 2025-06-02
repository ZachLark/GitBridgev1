"""GitBridgev1 Agent Framework Package."""

from .router import DelegationRouter, RoutePolicy, CLIDelegator
from .communication import AgentCommunicator, AgentMessage
from .agent import TaskProcessingAgent, AgentCapability

__version__ = '1.0.0'
__all__ = [
    'DelegationRouter',
    'RoutePolicy',
    'CLIDelegator',
    'AgentCommunicator',
    'AgentMessage',
    'TaskProcessingAgent',
    'AgentCapability'
] 