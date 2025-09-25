#!/usr/bin/env python3
"""
Simplified Orchestration Tool - Delegates to MCP Server.
All heavy lifting is done by the Orchestration MCP Server.
"""

import grpc
import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add path for proto imports
ORCHESTRATION_PATH = Path.home() / "repos" / "claude_mcp" / "orchestration_mcp"
if ORCHESTRATION_PATH.exists():
    sys.path.insert(0, str(ORCHESTRATION_PATH))
    try:
        from proto import conductor_pb2, conductor_pb2_grpc
    except ImportError:
        print("Error: Orchestration MCP proto not found. Ensure MCP server is built.")
        sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class SimplifiedOrchestrator:
    """Thin orchestrator that delegates to MCP server."""

    def __init__(self, mcp_host: str = "localhost", mcp_port: int = 50053):
        """Initialize connection to MCP server."""
        self.mcp_host = mcp_host
        self.mcp_port = mcp_port
        self.channel = None
        self.conductor = None
        self.current_task_id = None

    def connect(self) -> bool:
        """Connect to MCP server."""
        try:
            self.channel = grpc.insecure_channel(f"{self.mcp_host}:{self.mcp_port}")
            self.conductor = conductor_pb2_grpc.ConductorServiceStub(self.channel)

            # Test connection
            grpc.channel_ready_future(self.channel).result(timeout=2)
            logger.info(f"✓ Connected to Orchestration MCP Server at {self.mcp_host}:{self.mcp_port}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to connect to MCP server: {e}")
            logger.error("  Ensure the MCP server is running:")
            logger.error("  cd ~/repos/claude_mcp/orchestration_mcp && bash scripts/start_server.sh")
            return False

    def start_task(self, description: str) -> Optional[str]:
        """Start a new orchestration task."""
        if not self.conductor:
            logger.error("Not connected to MCP server")
            return None

        try:
            response = self.conductor.StartTask(conductor_pb2.StartTaskRequest(
                description=description,
                working_directory=os.getcwd()
            ))

            self.current_task_id = response.task_id
            logger.info(f"✓ Started task: {response.task_id}")
            logger.info(f"  Description: {description[:100]}...")
            logger.info(f"  Namespace: {response.namespace}")

            return response.task_id

        except grpc.RpcError as e:
            logger.error(f"✗ Failed to start task: {e.details()}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get current task status from MCP."""
        if not self.conductor or not self.current_task_id:
            return {"active": False, "message": "No active task"}

        try:
            response = self.conductor.GetTaskStatus(conductor_pb2.GetTaskStatusRequest(
                task_id=self.current_task_id
            ))

            status = {
                "active": True,
                "task_id": response.task_info.task_id,
                "description": response.task_info.description,
                "phase": response.task_info.current_phase,
                "status": response.task_info.status,
                "agents": []
            }

            # Add agent statuses
            for agent in response.agents:
                status["agents"].append({
                    "id": agent.agent_id,
                    "type": agent.agent_type,
                    "module": agent.module,
                    "status": agent.status
                })

            # Add recent discoveries
            if response.recent_discoveries:
                status["discoveries"] = []
                for discovery in response.recent_discoveries[:5]:
                    status["discoveries"].append({
                        "agent": discovery.agent_id,
                        "message": discovery.discovery,
                        "severity": discovery.severity
                    })

            return status

        except grpc.RpcError as e:
            logger.error(f"✗ Failed to get status: {e.details()}")
            return {"active": False, "error": str(e)}

    def advance_phase(self, to_phase: int) -> bool:
        """Request phase advancement from MCP."""
        if not self.conductor or not self.current_task_id:
            logger.error("No active task")
            return False

        try:
            response = self.conductor.AdvancePhase(conductor_pb2.AdvancePhaseRequest(
                task_id=self.current_task_id,
                to_phase=to_phase,
                force=False  # Let MCP validate
            ))

            if response.success:
                logger.info(f"✓ Advanced to phase {response.new_phase}: {response.phase_name}")
            else:
                logger.warning(f"✗ Phase advancement blocked:")
                for result in response.validation_results:
                    logger.warning(f"  - {result}")

            return response.success

        except grpc.RpcError as e:
            logger.error(f"✗ Failed to advance phase: {e.details()}")
            return False

    def complete_task(self, commit: bool = False) -> Dict[str, Any]:
        """Complete task and get memory promotion results."""
        if not self.conductor or not self.current_task_id:
            return {"success": False, "message": "No active task"}

        try:
            response = self.conductor.CompleteTask(conductor_pb2.CompleteTaskRequest(
                task_id=self.current_task_id,
                commit_changes=commit,
                commit_message=f"Orchestrated task {self.current_task_id}"
            ))

            result = {
                "success": response.success,
                "duration_seconds": response.duration_seconds,
                "promoted_patterns": len(response.promoted_patterns),
                "memories_promoted": response.memory_stats.promoted_count,
                "memories_purged": response.memory_stats.purged_count
            }

            logger.info(f"✓ Task completed successfully")
            logger.info(f"  Duration: {result['duration_seconds']}s")
            logger.info(f"  Patterns promoted: {result['promoted_patterns']}")
            logger.info(f"  Memories promoted: {result['memories_promoted']}")
            logger.info(f"  Memories purged: {result['memories_purged']}")

            # Clear current task
            self.current_task_id = None

            return result

        except grpc.RpcError as e:
            logger.error(f"✗ Failed to complete task: {e.details()}")
            return {"success": False, "error": str(e)}

    def get_agent_context(self, agent_type: str, module: str) -> Dict[str, Any]:
        """Get simplified agent context from MCP."""
        if not self.conductor or not self.current_task_id:
            return {"error": "No active task"}

        try:
            response = self.conductor.GetAgentContext(conductor_pb2.GetAgentContextRequest(
                task_id=self.current_task_id,
                agent_type=agent_type,
                module=module,
                include_patterns=True
            ))

            # Return simplified context
            return {
                "task_id": self.current_task_id,
                "instructions": response.simplified_instructions,
                "mission": response.context.mission_summary,
                "phase": response.context.current_phase_info,
                "validation": dict(response.context.validation_commands),
                "patterns": dict(response.context.relevant_patterns)[:5] if response.context.relevant_patterns else {},
                "gotchas": list(response.context.gotchas)
            }

        except grpc.RpcError as e:
            logger.error(f"✗ Failed to get agent context: {e.details()}")
            return {"error": str(e)}

    def disconnect(self):
        """Disconnect from MCP server."""
        if self.channel:
            self.channel.close()
            logger.info("Disconnected from MCP server")


def main():
    """CLI interface for orchestration."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  orchestration_v2.py start <description>  - Start new task")
        print("  orchestration_v2.py status               - Get current status")
        print("  orchestration_v2.py advance <phase>      - Advance to phase")
        print("  orchestration_v2.py complete             - Complete task")
        print("  orchestration_v2.py context <agent> <module> - Get agent context")
        sys.exit(1)

    command = sys.argv[1]
    orch = SimplifiedOrchestrator()

    if not orch.connect():
        sys.exit(1)

    try:
        if command == "start" and len(sys.argv) > 2:
            description = " ".join(sys.argv[2:])
            task_id = orch.start_task(description)
            if task_id:
                print(f"Task started: {task_id}")

        elif command == "status":
            status = orch.get_status()
            print(json.dumps(status, indent=2))

        elif command == "advance" and len(sys.argv) > 2:
            phase = int(sys.argv[2])
            if orch.advance_phase(phase):
                print(f"Advanced to phase {phase}")

        elif command == "complete":
            result = orch.complete_task()
            print(json.dumps(result, indent=2))

        elif command == "context" and len(sys.argv) > 3:
            agent_type = sys.argv[2]
            module = sys.argv[3]
            context = orch.get_agent_context(agent_type, module)
            print(json.dumps(context, indent=2))

        else:
            print(f"Unknown command: {command}")

    finally:
        orch.disconnect()


if __name__ == "__main__":
    main()