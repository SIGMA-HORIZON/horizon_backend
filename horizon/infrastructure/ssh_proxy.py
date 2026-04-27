import asyncio
import logging
import paramiko
from fastapi import WebSocket, WebSocketDisconnect
import io

logger = logging.getLogger(__name__)

async def proxy_ssh(
    websocket: WebSocket,
    host: str,
    username: str,
    private_key_str: str = None,
    password: str = None,
    port: int = 22
):
    """
    Proxy an SSH session over WebSocket using paramiko.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Load private key if provided
        pkey = None
        if private_key_str:
            try:
                # Try Ed25519 (default for Horizon)
                pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(private_key_str))
            except Exception:
                try:
                    # Fallback to RSA
                    pkey = paramiko.RSAKey.from_private_key(io.StringIO(private_key_str))
                except Exception as key_err:
                    logger.error(f"Failed to load SSH private key: {key_err}")
                    await websocket.close(code=1011, reason="Invalid SSH key format")
                    return

        # Connect to SSH
        logger.info(f"Connecting SSH to {host}:{port} as {username}")
        client.connect(
            hostname=host,
            port=port,
            username=username,
            pkey=pkey,
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        # Open interactive shell
        channel = client.invoke_shell(term='xterm', width=80, height=24)
        channel.setblocking(0)
        
        logger.info(f"SSH Session established for {host}")
        
        async def forward_to_ssh():
            try:
                while True:
                    message = await websocket.receive_text()
                    # Handle resize signal if we decide to send it as JSON
                    if message.startswith("{") and message.endswith("}"):
                        import json
                        try:
                            data = json.loads(message)
                            if data.get("type") == "resize":
                                channel.resize_pty(
                                    width=data.get("cols", 80),
                                    height=data.get("rows", 24)
                                )
                                continue
                        except:
                            pass
                    
                    if channel.send_ready():
                        channel.send(message)
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
            except Exception as e:
                logger.error(f"Error in forward_to_ssh: {e}")
            finally:
                if not channel.closed:
                    channel.close()

        async def forward_to_websocket():
            try:
                while True:
                    await asyncio.sleep(0.01) # Small sleep to prevent busy loop
                    if channel.recv_ready():
                        data = channel.recv(4096)
                        if not data:
                            break
                        await websocket.send_text(data.decode('utf-8', errors='replace'))
                    if channel.exit_status_ready():
                        break
            except Exception as e:
                logger.error(f"Error in forward_to_websocket: {e}")
            finally:
                await websocket.close()

        # Run both tasks
        await asyncio.gather(forward_to_ssh(), forward_to_websocket())

    except Exception as e:
        logger.error(f"SSH Proxy error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
    finally:
        client.close()
