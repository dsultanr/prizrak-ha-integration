"""Prizrak monitoring client for Home Assistant."""
import asyncio
import websockets
import json
import requests
import urllib.parse
import logging
from typing import Optional, Dict, Any, Callable
import time
import hashlib
import base64

_LOGGER = logging.getLogger(__name__)


class PrizrakClient:
    """Client for Prizrak monitoring system."""

    def __init__(
        self,
        email: str,
        password: str,
        state_callback: Callable[[int, Dict[str, Any]], None]
    ):
        """Initialize the client.

        Args:
            email: User email for authentication
            password: User password
            state_callback: Callback function for device state updates
        """
        self.login = email
        self.password = password
        self._state_callback = state_callback

        self.base_url = "https://monitoring.tecel.ru"
        self.passport_url = f"{self.base_url}/passport/api"
        self.ws_url = "wss://monitoring.tecel.ru"

        self.auth_token: Optional[str] = None
        self.connection_id: Optional[str] = None
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 999999
        self.reconnect_delay = 5
        self.invocation_counter = 0
        self.devices = []
        self.device_states = {}
        self.last_auth_time = 0
        self.auth_validity_hours = 12
        self.last_message_time = 0
        self.last_event_time = 0
        self.message_timeout = 60
        self.event_timeout = 120  # Если нет EventObject 2 минуты - переподключение
        self.ping_interval = 15
        self.last_ping_time = 0

        # Event to signal when devices are ready
        self.devices_ready = asyncio.Event()

        # Track pending command invocations
        self.pending_invocations: Dict[str, asyncio.Future] = {}

    def _get_fingerprint_token(self) -> str:
        """Generate fingerprint token for vtoken."""
        data = {
            "VTokenKey": "x-vtoken",
            "FingerPrint": hashlib.md5("browser_fingerprint".encode()).hexdigest(),
            "UniqId": "mit9hov5mit9hov6mit9hov7mit9hov8",
            "AppVersion": "268.0.0.0",
            "Service": ""
        }
        return base64.b64encode(json.dumps(data).encode()).decode()

    def _authenticate_sync(self) -> bool:
        """Synchronous authentication - internal use only."""
        try:
            _LOGGER.info(f"Authenticating user: {self.login}")

            headers = {
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'x-vtoken': self._get_fingerprint_token()
            }

            # Step 1: CheckLogin
            check_payload = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "CheckLogin",
                "params": {
                    "login": self.login,
                    "language_code": "EN"
                }
            }

            response = requests.post(self.passport_url, json=check_payload, headers=headers, timeout=10)
            if response.status_code != 200:
                _LOGGER.error(f"CheckLogin failed: {response.status_code}")
                return False

            check_result = response.json()
            _LOGGER.debug(f"CheckLogin result: {check_result}")

            # Step 2: Authorization
            auth_payload = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "Authorization",
                "params": {
                    "login": self.login,
                    "password": self.password,
                    "forever": True,
                    "language_code": "EN"
                }
            }

            response = requests.post(self.passport_url, json=auth_payload, headers=headers, timeout=10)
            if response.status_code != 200:
                _LOGGER.error(f"Authorization failed: {response.status_code}")
                return False

            auth_result = response.json()
            _LOGGER.debug(f"Auth response: {auth_result}")

            # Check for x-atoken in response headers
            x_atoken = response.headers.get('x-atoken') or response.headers.get('X-AToken')

            if x_atoken:
                _LOGGER.info(f"Got Atoken from headers")
                self.auth_token = x_atoken
                self.last_auth_time = time.time()
                return True

            # Check if authorization was successful
            if 'result' in auth_result:
                result = auth_result['result']

                # Check for atoken in result
                if 'atoken' in result:
                    self.auth_token = result['atoken']
                    _LOGGER.info(f"Got Atoken from result")
                    self.last_auth_time = time.time()
                    return True

                # Session created successfully
                if 'session_id' in result:
                    session_id = result['session_id']
                    _LOGGER.info(f"Session created: {session_id}")
                    self.auth_token = session_id
                    self.last_auth_time = time.time()
                    _LOGGER.warning("Using session_id as Atoken (may not work)")
                    return True
                else:
                    _LOGGER.error(f"No session_id or atoken in response: {result}")
                    return False
            else:
                _LOGGER.error(f"No result in response: {auth_result}")
                return False

        except Exception as e:
            _LOGGER.error(f"Authentication error: {e}")
            return False

    async def authenticate(self) -> bool:
        """Authenticate using login/password via passport API (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._authenticate_sync)

    def check_auth_validity(self) -> bool:
        """Check if we need to re-authenticate."""
        if not self.auth_token:
            return False

        hours_since_auth = (time.time() - self.last_auth_time) / 3600
        if hours_since_auth > self.auth_validity_hours:
            _LOGGER.info(f"Token expired ({hours_since_auth:.1f}h), re-authenticating...")
            return False

        return True

    def _create_auth_payload(self) -> Dict[str, Any]:
        return {
            "Type": 2154785295,
            "Atoken": self.auth_token,
            "ClientData": {
                "AppName": "Home Assistant Prizrak",
                "AppVersion": "1.0.0",
                "AppHost": "monitoring.tecel.ru",
                "IsUserDataAvailable": True,
                "AdditionalInfo": {}
            },
            "Lang": "ru"
        }

    def _get_headers(self) -> Dict[str, str]:
        auth_payload = json.dumps(self._create_auth_payload())
        return {
            'accept': '*/*',
            'authorization': f'Bearer {auth_payload}',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'x-signalr-user-agent': 'Microsoft SignalR/7.0'
        }

    def _negotiate_connection_sync(self) -> Optional[str]:
        """Synchronous connection negotiation - internal use only."""
        negotiate_url = f"{self.base_url}/api/Control/negotiate?negotiateVersion=1"
        try:
            _LOGGER.info("Negotiating SignalR connection...")
            response = requests.post(negotiate_url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                connection_token = data.get('connectionToken')
                _LOGGER.info(f"Connection negotiated successfully")
                return connection_token
            else:
                _LOGGER.error(f"Negotiate failed: {response.status_code}")
                return None
        except Exception as e:
            _LOGGER.error(f"Negotiation error: {e}")
            return None

    async def negotiate_connection(self) -> Optional[str]:
        """Negotiate SignalR connection (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._negotiate_connection_sync)

    async def delete_connection(self, connection_id: str):
        """Delete an existing connection on the server."""
        try:
            delete_url = f"{self.base_url}/api/Control?id={connection_id}"
            _LOGGER.info(f"Attempting to delete existing connection...")

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.delete(delete_url, headers=self._get_headers(), timeout=5)
            )

            if response.status_code in [200, 204, 404]:
                _LOGGER.info(f"Existing connection deleted or already gone (HTTP {response.status_code})")
                return True
            else:
                _LOGGER.warning(f"Delete connection returned HTTP {response.status_code}")
                return False
        except Exception as e:
            _LOGGER.warning(f"Failed to delete connection: {e}")
            return False

    def _cleanup_pending_invocations(self):
        """Cancel all pending invocations (called on disconnect/reconnect)."""
        if self.pending_invocations:
            _LOGGER.warning(f"Cleaning up {len(self.pending_invocations)} pending invocations")
            for invocation_id, future in self.pending_invocations.items():
                if not future.done():
                    future.set_result({
                        "success": False,
                        "error": "Connection lost"
                    })
            self.pending_invocations.clear()

    async def connect_websocket(self) -> bool:
        # Cleanup any pending commands from previous connection
        self._cleanup_pending_invocations()

        if not self.connection_id:
            self.connection_id = await self.negotiate_connection()
            if not self.connection_id:
                return False

        auth_payload = json.dumps(self._create_auth_payload())
        encoded_auth = urllib.parse.quote(auth_payload)
        ws_url = f"{self.ws_url}/api/Control?id={self.connection_id}&access_token={encoded_auth}"

        ws_headers = {'Origin': 'https://monitoring.tecel.ru'}

        try:
            _LOGGER.info("Connecting to WebSocket...")
            self.websocket = await websockets.connect(ws_url, additional_headers=ws_headers, compression=None)
            _LOGGER.info("WebSocket connected!")
            self.reconnect_attempts = 0
            return True
        except Exception as e:
            # Duck-typing: Check if the exception has a status_code attribute
            if hasattr(e, "status_code"):
                status_code = e.status_code
                if status_code == 404:
                    _LOGGER.warning(f"WebSocket rejected (HTTP 404) - forcing re-auth...")
                    self.connection_id = None
                    self.auth_token = None
                elif status_code == 401:
                    _LOGGER.warning(f"WebSocket rejected (HTTP 401) - forcing re-auth...")
                    self.auth_token = None
                elif status_code == 409:
                    _LOGGER.warning(f"WebSocket rejected (HTTP 409) - connection exists...")
                    # Try to delete the existing connection
                    old_conn_id = self.connection_id
                    # Run delete in a new task to avoid blocking the reconnect loop
                    asyncio.create_task(self.delete_connection(old_conn_id))
                    # Force new negotiation immediately
                    self.connection_id = None
                    await asyncio.sleep(2)  # Give server time to process delete
                else:
                    _LOGGER.error(f"WebSocket rejected with unhandled code: HTTP {status_code}")
            else:
                # Not an HTTP status error, log as a generic WebSocket error
                _LOGGER.error(f"WebSocket error: {type(e).__name__}: {e}")

            return False

    async def send_handshake(self):
        handshake = {"protocol": "json", "version": 1}
        await self.websocket.send(json.dumps(handshake) + '\x1e')
        _LOGGER.info("Handshake sent")

    async def send_ping(self):
        ping_msg = {"type": 6}
        await self.websocket.send(json.dumps(ping_msg) + '\x1e')
        _LOGGER.debug("Ping sent")

    async def get_devices(self):
        self.invocation_counter += 1
        request = {
            "type": 1,
            "invocationId": str(self.invocation_counter),
            "target": "GetDevices",
            "arguments": [{"registrations": True, "custom_fields": True, "possible_commands": True}]
        }
        await self.websocket.send(json.dumps(request, ensure_ascii=False) + '\x1e')
        _LOGGER.info(f"GetDevices request sent")

    async def watch_devices(self, device_ids):
        self.invocation_counter += 1
        request = {
            "type": 1,
            "invocationId": str(self.invocation_counter),
            "target": "WatchDevice",
            "arguments": [{"device_ids": device_ids}]
        }
        await self.websocket.send(json.dumps(request, ensure_ascii=False) + '\x1e')
        _LOGGER.info(f"Subscribed to devices: {device_ids}")

    async def send_command(self, device_id: int, command: str, timeout: float = 10.0):
        """Send command to device via WebSocket and wait for response.

        Args:
            device_id: Device ID to send command to
            command: Command name (GuardOn, GuardOff, AutolaunchOn, AutolaunchOff)
            timeout: Maximum time to wait for response (default 10s)

        Returns:
            True if command was sent and server confirmed success
            False if command failed or timed out
        """
        if not self.websocket:
            _LOGGER.error("WebSocket not connected")
            return False

        self.invocation_counter += 1
        invocation_id = str(self.invocation_counter)

        request = {
            "type": 1,
            "invocationId": invocation_id,
            "target": command,
            "arguments": [{"device_id": device_id}]
        }

        # Create Future for waiting response
        future = asyncio.Future()
        self.pending_invocations[invocation_id] = future

        try:
            # Send command with timeout
            await asyncio.wait_for(
                self.websocket.send(json.dumps(request, ensure_ascii=False) + '\x1e'),
                timeout=5.0
            )
            _LOGGER.info(f"Sent command {command} to device {device_id} (invocationId={invocation_id})")

            # Wait for server response
            result = await asyncio.wait_for(future, timeout=timeout)

            if result.get("success", False):
                _LOGGER.info(f"Command {command} confirmed successful by server (invocationId={invocation_id})")
                return True
            else:
                error_msg = result.get("error", "Unknown error")
                _LOGGER.error(f"Command {command} failed: {error_msg} (invocationId={invocation_id})")
                return False

        except asyncio.TimeoutError:
            _LOGGER.error(f"Command {command} timeout - no response from server (invocationId={invocation_id})")
            return False
        except Exception as e:
            _LOGGER.error(f"Failed to send command {command}: {e} (invocationId={invocation_id})")
            return False
        finally:
            # Cleanup pending invocation
            self.pending_invocations.pop(invocation_id, None)

    def handle_event_object(self, arguments):
        """Handle EventObject - device state updates."""
        if not arguments:
            return

        # Update timestamp of last EventObject
        self.last_event_time = time.time()

        event_data = arguments[0]
        device_id = event_data.get('device_id')
        device_state = event_data.get('device_state', {})

        if device_id:
            if device_id not in self.device_states:
                self.device_states[device_id] = {}

            self.device_states[device_id].update(device_state)

            # Call Home Assistant callback
            try:
                self._state_callback(device_id, device_state)
            except Exception as e:
                _LOGGER.error(f"Error in state callback: {e}")

            # Log important info
            serial = device_state.get('serial_no', 'Unknown')
            conn_state = device_state.get('connection_state')

            _LOGGER.info(f"Device Update [{device_id}] {serial}")

            if conn_state:
                _LOGGER.info(f"  Connection: {conn_state}")

            # Security status
            guard = device_state.get('guard')
            alarm = device_state.get('alarm')
            if guard:
                _LOGGER.info(f"  Guard: {guard}")
            if alarm and alarm not in ["Unknown", "None"]:
                _LOGGER.warning(f"  ALARM: {alarm}")

    async def receive_messages(self):
        """Receive and process WebSocket messages."""
        try:
            self.last_message_time = time.time()

            async for message in self.websocket:
                try:
                    self.last_message_time = time.time()

                    if isinstance(message, bytes):
                        message = message.decode('utf-8')

                    cleaned = message.strip('\x1e')
                    if not cleaned:
                        continue

                    data = json.loads(cleaned)
                    msg_type = data.get('type')

                    if msg_type == 6:
                        _LOGGER.debug("Ping received, sending pong")
                        await self.send_ping()

                    elif msg_type == 1:
                        target = data.get('target')
                        arguments = data.get('arguments', [])

                        if target == "EventObject":
                            self.handle_event_object(arguments)
                        else:
                            _LOGGER.debug(f"Invocation: {target}")

                    elif msg_type == 3:
                        # Type 3 = Completion (response to invocation)
                        invocation_id = data.get('invocationId')
                        result = data.get('result')
                        error = data.get('error')

                        _LOGGER.debug(f"Response to invocation {invocation_id}: error={error}")

                        # Check if this is a pending command waiting for response
                        if invocation_id in self.pending_invocations:
                            future = self.pending_invocations[invocation_id]
                            if not future.done():
                                if error:
                                    # Server returned error
                                    future.set_result({
                                        "success": False,
                                        "error": error
                                    })
                                else:
                                    # Command successful
                                    future.set_result({
                                        "success": True,
                                        "result": result
                                    })

                        # Handle GetDevices response
                        if result and isinstance(result, dict):
                            devices_data = result.get('data', {}).get('devices', [])
                            if devices_data:
                                self.devices = devices_data
                                _LOGGER.info(f"Found {len(devices_data)} device(s):")
                                for dev in devices_data:
                                    _LOGGER.info(f"   • {dev.get('name')} ({dev.get('model')}) - ID: {dev.get('device_id')}")

                                device_ids = [d['device_id'] for d in devices_data]
                                await self.watch_devices(device_ids)

                                # Signal that devices are ready
                                if not self.devices_ready.is_set():
                                    self.devices_ready.set()
                                    _LOGGER.info("Devices ready event set")

                except json.JSONDecodeError:
                    _LOGGER.debug(f"Non-JSON message")
                except Exception as e:
                    _LOGGER.error(f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            _LOGGER.warning("Connection closed")
            raise
        except asyncio.TimeoutError:
            _LOGGER.warning("Connection timeout - no messages received")
            raise

    async def send_proactive_pings(self):
        """Send ping to server every 15 seconds to keep connection alive."""
        while self.running:
            await asyncio.sleep(self.ping_interval)

            if self.websocket:
                try:
                    await self.send_ping()
                    self.last_ping_time = time.time()
                    _LOGGER.debug(f"Proactive ping sent (keep-alive)")
                except Exception as e:
                    _LOGGER.error(f"Failed to send proactive ping: {e}")
                    break

    async def check_connection_health(self):
        """Monitor connection health and reconnect if needed."""
        while self.running:
            await asyncio.sleep(10)

            if self.websocket:
                # Check for any messages (including ping/pong)
                if self.last_message_time > 0:
                    time_since_last_msg = time.time() - self.last_message_time

                    if time_since_last_msg > self.message_timeout:
                        _LOGGER.warning(f"No messages for {int(time_since_last_msg)}s - connection may be dead")
                        _LOGGER.info("Initiating reconnection...")

                        try:
                            await self.websocket.close()
                        except:
                            pass
                        break

                # Check for EventObject specifically (device state updates)
                if self.last_event_time > 0:
                    time_since_last_event = time.time() - self.last_event_time

                    if time_since_last_event > self.event_timeout:
                        _LOGGER.warning(f"No EventObject updates for {int(time_since_last_event)}s - watch may be broken")
                        _LOGGER.info("Initiating reconnection to re-subscribe...")

                        try:
                            await self.websocket.close()
                        except:
                            pass
                        break

    async def run(self):
        """Main run loop with auto-recovery."""
        self.running = True

        # Initial authentication
        if not await self.authenticate():
            _LOGGER.error("Initial authentication failed!")
            return

        while self.running:
            try:
                # Check if token is still valid
                if not self.check_auth_validity():
                    if not await self.authenticate():
                        _LOGGER.error("Re-authentication failed, retrying in 30s...")
                        await asyncio.sleep(30)
                        continue

                # Connect to WebSocket
                if await self.connect_websocket():
                    await self.send_handshake()
                    await asyncio.sleep(0.5)
                    await self.get_devices()

                    # Start background tasks
                    ping_task = asyncio.create_task(self.send_proactive_pings())
                    health_task = asyncio.create_task(self.check_connection_health())

                    try:
                        await self.receive_messages()
                    finally:
                        # Cancel background tasks when receive_messages exits
                        ping_task.cancel()
                        health_task.cancel()
                        try:
                            await ping_task
                        except asyncio.CancelledError:
                            pass
                        try:
                            await health_task
                        except asyncio.CancelledError:
                            pass
                else:
                    # Connection failed, wait before retry with exponential backoff
                    delay = min(self.reconnect_delay * (2 ** min(self.reconnect_attempts, 5)), 60)
                    _LOGGER.warning(f"WebSocket connection failed, retrying in {delay}s (attempt {self.reconnect_attempts + 1})...")
                    self.reconnect_attempts += 1
                    await asyncio.sleep(delay)
                    continue

            except websockets.exceptions.ConnectionClosed:
                _LOGGER.warning(f"Connection closed, reconnecting in {self.reconnect_delay}s...")
                self.reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay)
                self.connection_id = None

            except asyncio.TimeoutError:
                _LOGGER.warning(f"Connection timeout, reconnecting in {self.reconnect_delay}s...")
                self.reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay)
                self.connection_id = None

            except asyncio.CancelledError:
                _LOGGER.info("Client task cancelled")
                self.running = False
                break

            except Exception as e:
                _LOGGER.error(f"Error: {e}")
                self.reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay)
                self.connection_id = None

        if self.websocket:
            await self.websocket.close()

        _LOGGER.info("Client stopped")

    def stop(self):
        """Stop the client."""
        self.running = False
