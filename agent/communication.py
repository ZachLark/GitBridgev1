#!/usr/bin/env python3
"""Agent communication system for GitBridge."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid

@dataclass
class AgentMessage:
    """Represents a message between agents."""
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: str
    requires_response: bool = False
    correlation_id: Optional[str] = None

class AgentCommunicator:
    """Handles communication between agents."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"communication.{agent_id}")
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.message_history: List[AgentMessage] = []
        self.connected_agents: Dict[str, datetime] = {}
        
        # Configure logging
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"logs/communication_{agent_id}.log")
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler
        self.logger.info(f"Registered handler for message type: {message_type}")
    
    async def send_message(
        self,
        recipient_id: str,
        message_type: str,
        content: Dict[str, Any],
        requires_response: bool = False
    ) -> Optional[AgentMessage]:
        """Send a message to another agent."""
        try:
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                message_type=message_type,
                content=content,
                timestamp=datetime.now().isoformat(),
                requires_response=requires_response
            )
            
            # Simulate message delivery
            await self._deliver_message(message)
            
            # Store in history
            self.message_history.append(message)
            
            # Wait for response if required
            if requires_response:
                response_future = asyncio.Future()
                self.pending_responses[message.message_id] = response_future
                try:
                    response = await asyncio.wait_for(response_future, timeout=30.0)
                    return response
                except asyncio.TimeoutError:
                    self.logger.warning(f"Response timeout for message {message.message_id}")
                    return None
                finally:
                    self.pending_responses.pop(message.message_id, None)
            
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return None
    
    async def _deliver_message(self, message: AgentMessage):
        """Simulate message delivery to recipient."""
        # In a real system, this would use actual message transport
        # For now, we simulate local delivery
        await asyncio.sleep(0.01)  # Simulate network delay
        
        # Log delivery
        self.logger.info(
            f"Delivered message {message.message_id} to {message.recipient_id}"
        )
        
        # Store message for recipient
        message_file = Path(f"messages/{message.recipient_id}/inbox/{message.message_id}.json")
        message_file.parent.mkdir(parents=True, exist_ok=True)
        
        with message_file.open('w') as f:
            json.dump(asdict(message), f, indent=2)
    
    async def process_incoming_messages(self):
        """Process incoming messages from inbox."""
        while True:
            try:
                inbox = Path(f"messages/{self.agent_id}/inbox")
                if inbox.exists():
                    for message_file in inbox.glob("*.json"):
                        try:
                            with message_file.open('r') as f:
                                message_data = json.load(f)
                            
                            message = AgentMessage(**message_data)
                            
                            # Handle message
                            if message.message_type in self.message_handlers:
                                handler = self.message_handlers[message.message_type]
                                response = await handler(message)
                                
                                # Send response if required
                                if message.requires_response and response:
                                    response_message = AgentMessage(
                                        message_id=str(uuid.uuid4()),
                                        sender_id=self.agent_id,
                                        recipient_id=message.sender_id,
                                        message_type=f"{message.message_type}_response",
                                        content=response,
                                        timestamp=datetime.now().isoformat(),
                                        correlation_id=message.message_id
                                    )
                                    await self._deliver_message(response_message)
                            
                            # Archive processed message
                            archive_dir = Path(f"messages/{self.agent_id}/archive")
                            archive_dir.mkdir(exist_ok=True)
                            message_file.rename(archive_dir / message_file.name)
                            
                        except Exception as e:
                            self.logger.error(f"Error processing message {message_file}: {str(e)}")
                            
                            # Move to error folder
                            error_dir = Path(f"messages/{self.agent_id}/errors")
                            error_dir.mkdir(exist_ok=True)
                            message_file.rename(error_dir / message_file.name)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {str(e)}")
                await asyncio.sleep(5)  # Back off on error
    
    async def broadcast_state_change(self, state_update: Dict[str, Any]):
        """Broadcast state change to all connected agents."""
        for agent_id in self.connected_agents:
            await self.send_message(
                recipient_id=agent_id,
                message_type="state_change",
                content=state_update
            )
    
    def register_agent(self, agent_id: str):
        """Register a connected agent."""
        self.connected_agents[agent_id] = datetime.now()
        self.logger.info(f"Registered connected agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister a connected agent."""
        if agent_id in self.connected_agents:
            del self.connected_agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    def get_communication_status(self) -> Dict[str, Any]:
        """Get current communication system status."""
        return {
            "connected_agents": len(self.connected_agents),
            "message_handlers": list(self.message_handlers.keys()),
            "pending_responses": len(self.pending_responses),
            "message_history_size": len(self.message_history)
        } 