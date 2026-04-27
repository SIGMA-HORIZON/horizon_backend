"""
VNC WebSocket proxy for Horizon → Proxmox bridging.

Proxmox's vncwebsocket endpoint requires a PVEAuthCookie obtained via username/password
login — API tokens cannot authenticate this endpoint. Additionally, the VNC ticket
and the session cookie must come from the SAME login session.

This module handles the full flow:
1. Login as root@pam to get a PVEAuthCookie + CSRF token
2. Use that session to request a fresh VNC ticket + port
3. Open the Proxmox vncwebsocket using that session cookie + VNC ticket
4. Bidirectionally proxy bytes between the browser and Proxmox
"""
import asyncio
import logging
import ssl
import urllib.parse
import urllib.request
import json

logger = logging.getLogger(__name__)


def _proxmox_session_login(proxmox_host: str, root_user: str, root_password: str, verify_ssl: bool = False) -> tuple[str, str]:
    """Login and return (pve_cookie, csrf_token)."""
    ctx = ssl.create_default_context()
    if not verify_ssl:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    data = urllib.parse.urlencode({"username": root_user, "password": root_password}).encode()
    req = urllib.request.Request(
        f"https://{proxmox_host}:8006/api2/json/access/ticket",
        method="POST",
        data=data,
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        payload = json.loads(resp.read())["data"]
    return payload["ticket"], payload["CSRFPreventionToken"]


def _get_vnc_ticket_with_session(
    proxmox_host: str,
    node: str,
    vmid: int,
    pve_cookie: str,
    csrf_token: str,
    verify_ssl: bool = False,
) -> tuple[str, str]:
    """Get a VNC ticket using a session cookie. Returns (ticket, port)."""
    ctx = ssl.create_default_context()
    if not verify_ssl:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        f"https://{proxmox_host}:8006/api2/json/nodes/{node}/qemu/{vmid}/vncproxy",
        method="POST",
        headers={
            "Cookie": f"PVEAuthCookie={pve_cookie}",
            "CSRFPreventionToken": csrf_token,
            "Content-Type": "application/json",
        },
        data=b'{"websocket":1}',
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read())["data"]
    return data["ticket"], str(data["port"])


async def proxy_vnc(
    websocket,
    proxmox_host: str,
    node: str,
    vmid: int,
    port: str,          # ignored — we fetch a fresh ticket/port via root session
    ticket: str,        # ignored — we fetch a fresh ticket/port via root session
    root_user: str = "root@pam",
    root_password: str = "",
    verify_ssl: bool = False,
    **kwargs,
):
    """
    Proxy a VNC WebSocket connection from the browser to Proxmox.

    The incoming `ticket` and `port` from the frontend are ignored because
    Proxmox requires the VNC ticket and the WebSocket session cookie to come
    from the SAME login session.  We therefore do a fresh root@pam login here,
    get a new VNC ticket from that session, and use the same session cookie for
    the WebSocket handshake.
    """
    import websockets

    if not root_password:
        logger.error("VNC proxy: PROXMOX_ROOT_PASSWORD is not configured")
        try:
            await websocket.close(code=1011, reason="Server misconfigured")
        except Exception:
            pass
        return

    # 1. Login as root@pam to get a session
    try:
        pve_cookie, csrf_token = _proxmox_session_login(proxmox_host, root_user, root_password, verify_ssl)
        logger.info(f"VNC proxy: obtained PVEAuthCookie for vmid={vmid}")
    except Exception as e:
        logger.error(f"VNC proxy: login failed: {e}")
        try:
            await websocket.close(code=1011, reason="Proxmox login failed")
        except Exception:
            pass
        return

    # 2. Get a fresh VNC ticket from the same session
    try:
        vnc_ticket, vnc_port = _get_vnc_ticket_with_session(
            proxmox_host, node, vmid, pve_cookie, csrf_token, verify_ssl
        )
        logger.info(f"VNC proxy: got VNC ticket port={vnc_port} for vmid={vmid}")
    except Exception as e:
        logger.error(f"VNC proxy: failed to get VNC ticket: {e}")
        try:
            await websocket.close(code=1011, reason="Could not get VNC ticket")
        except Exception:
            pass
        return

    # 3. Build the Proxmox WS URL
    encoded_ticket = urllib.parse.quote(vnc_ticket, safe="")
    px_url = (
        f"wss://{proxmox_host}:8006/api2/json/nodes/{node}/qemu/{vmid}"
        f"/vncwebsocket?port={vnc_port}&vncticket={encoded_ticket}"
    )

    ssl_ctx = ssl.create_default_context()
    if not verify_ssl:
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

    logger.info(f"VNC proxy connecting WS: {px_url[:80]}...")

    try:
        async with websockets.connect(
            px_url,
            subprotocols=["binary"],
            ssl=ssl_ctx,
            additional_headers={"Cookie": f"PVEAuthCookie={pve_cookie}"},
        ) as px_ws:
            logger.info(f"VNC proxy bridged: browser ↔ Proxmox vmid={vmid}")

            async def forward_to_proxmox():
                try:
                    async for message in websocket.iter_bytes():
                        await px_ws.send(message)
                except Exception as e:
                    logger.debug(f"Frontend→Proxmox ended: {e}")

            async def forward_to_frontend():
                try:
                    async for message in px_ws:
                        if isinstance(message, str):
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except Exception as e:
                    logger.debug(f"Proxmox→Frontend ended: {e}")

            done, pending = await asyncio.wait(
                [
                    asyncio.ensure_future(forward_to_proxmox()),
                    asyncio.ensure_future(forward_to_frontend()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            logger.info(f"VNC proxy session ended for vmid={vmid}")

    except Exception as e:
        logger.error(f"VNC Proxy WS error for vmid={vmid}: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass
