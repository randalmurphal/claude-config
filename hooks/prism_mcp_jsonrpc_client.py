#!/opt/envs/py3.13/bin/python
"""
PRISM MCP JSON-RPC Client
Simple, clean interface to PRISM MCP server via JSON-RPC over stdio.
No gRPC, no proto files, just JSON.
"""

import json
import subprocess
import logging
import threading
import queue
import atexit
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class PrismMCPClient:
    """Clean JSON-RPC client for PRISM MCP server."""

    def __init__(self):
        """Initialize MCP client with persistent subprocess."""
        self.mcp_binary = Path.home() / "repos" / "claude_mcp" / "prism_mcp" / "bin" / "prism-mcp-launcher"
        self.process = None
        self.request_id = 0
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self._lock = threading.Lock()
        self._connected = False

        # Start the connection
        self._connect()

        # Register cleanup
        atexit.register(self.close)

    def _connect(self) -> bool:
        """Start MCP server subprocess and reader thread."""
        try:
            if not self.mcp_binary.exists():
                logger.error(f"MCP binary not found at {self.mcp_binary}")
                return False

            # Start MCP server as subprocess
            self.process = subprocess.Popen(
                [str(self.mcp_binary)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # Suppress stderr logs
                text=True,
                bufsize=1  # Line buffered
            )

            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_responses, daemon=True)
            self.reader_thread.start()

            self._connected = True
            logger.info("MCP server connected via JSON-RPC")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self._connected = False
            return False

    def _read_responses(self):
        """Read responses from MCP server stdout."""
        if not self.process:
            return

        try:
            for line in self.process.stdout:
                if line.strip():
                    try:
                        response = json.loads(line)
                        self.response_queue.put(response)
                    except json.JSONDecodeError:
                        # Skip non-JSON lines (logs, etc.)
                        pass
        except Exception as e:
            logger.error(f"Reader thread error: {e}")

    def _call_method(self, method: str, params: Optional[Dict] = None) -> Any:
        """Send JSON-RPC request and get response."""
        if not self._connected or not self.process:
            if not self._connect():
                raise Exception("MCP server not connected")

        with self._lock:
            self.request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": method,
                "params": params or {}
            }

            try:
                # Send request
                self.process.stdin.write(json.dumps(request) + "\n")
                self.process.stdin.flush()

                # Wait for response with matching ID
                timeout = 30  # seconds
                import time
                start = time.time()

                while time.time() - start < timeout:
                    try:
                        response = self.response_queue.get(timeout=0.1)
                        if response.get("id") == self.request_id:
                            if "error" in response:
                                raise Exception(f"MCP error: {response['error']}")
                            return response.get("result")
                    except queue.Empty:
                        continue

                raise Exception("Timeout waiting for MCP response")

            except Exception as e:
                logger.error(f"MCP call failed: {e}")
                raise

    def is_available(self) -> bool:
        """Check if MCP server is available."""
        try:
            # Try to list tools as a health check
            result = self._call_method("tools/list")
            return bool(result and "tools" in result)
        except:
            return False

    def store_memory(self, content: str, tier: str = "LONGTERM", metadata: Optional[Dict] = None) -> bool:
        """Store memory in PRISM."""
        try:
            result = self._call_method("tools/call", {
                "name": "mcp__prism__store_memory",
                "arguments": {
                    "content": content,
                    "tier": tier.upper(),
                    "metadata": metadata or {}
                }
            })

            # Parse nested response
            if result and "content" in result:
                content_text = result["content"][0]["text"]
                response = json.loads(content_text)
                return response.get("success", False)
            return False

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False

    def search_memory(self, query: str, limit: int = 10, tier: Optional[str] = None) -> List[Dict]:
        """Search PRISM memory."""
        try:
            params = {
                "name": "mcp__prism__search_memory",
                "arguments": {
                    "query": query,
                    "limit": limit
                }
            }
            if tier:
                params["arguments"]["tier"] = tier.upper()

            result = self._call_method("tools/call", params)

            # Parse nested response
            if result and "content" in result:
                content_text = result["content"][0]["text"]
                response = json.loads(content_text)
                return response.get("results", [])
            return []

        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []

    def analyze(self, text: str) -> Optional[Dict]:
        """Analyze text using PRISM reasoning."""
        try:
            result = self._call_method("tools/call", {
                "name": "mcp__prism__analyze",
                "arguments": {"text": text}
            })

            # Parse nested response
            if result and "content" in result:
                content_text = result["content"][0]["text"]
                return json.loads(content_text)
            return None

        except Exception as e:
            logger.error(f"Failed to analyze: {e}")
            return None

    def detect_hallucination(self, text: str, confidence_threshold: float = 0.8) -> Optional[Dict]:
        """Detect hallucination risk."""
        try:
            result = self._call_method("tools/call", {
                "name": "mcp__prism__detect_hallucination",
                "arguments": {
                    "text": text,
                    "confidence_threshold": confidence_threshold
                }
            })

            # Parse nested response
            if result and "content" in result:
                content_text = result["content"][0]["text"]
                response = json.loads(content_text)
                return {
                    'risk_level': response.get('verification', {}).get('recommendation', 'unknown'),
                    'risk_score': response.get('verification', {}).get('risk_score', 0),
                    'risk_factors': response.get('verification', {}).get('risk_factors', []),
                    'recommendation': response.get('verification', {}).get('recommendation', '')
                }
            return None

        except Exception as e:
            logger.error(f"Failed to detect hallucination: {e}")
            return None

    def calculate_semantic_drift(self, input_text: str, ground_truth: str) -> Optional[Dict]:
        """Calculate semantic drift between texts."""
        try:
            result = self._call_method("tools/call", {
                "name": "mcp__prism__semantic_residue",
                "arguments": {
                    "input_text": input_text,
                    "ground_truth": ground_truth
                }
            })

            # Parse nested response
            if result and "content" in result:
                content_text = result["content"][0]["text"]
                response = json.loads(content_text)
                return {
                    'drift_score': response.get('residue', 0),
                    'zone': response.get('zone', 'unknown'),
                    'confidence': response.get('confidence', 0)
                }
            return None

        except Exception as e:
            logger.error(f"Failed to calculate semantic drift: {e}")
            return None

    def close(self):
        """Close the MCP server connection."""
        self._connected = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                self.process.kill()
            self.process = None

# Singleton instance
_mcp_client = None

def get_mcp_client() -> PrismMCPClient:
    """Get or create MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = PrismMCPClient()
    return _mcp_client