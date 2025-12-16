#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WHR90 Ventilation Unit MQTT bridge 
Author: RuntimeError123 / L. Bosch
MIT License

- Retrieves temperature and fan status via EW11 (TCP).
- Publishes values to MQTT including Home Assistant discovery.
- TLS handling:
  * Plain MQTT (no TLS)
  * TLS with CA only
  * Mutual TLS (CA + client cert/key)
  * Optional insecure mode for testing
- Publishes binary sensors (supply/exhaust active).
- Configuration is loaded from environment variables.
"""

import os
import ssl
import socket
import time
import signal
import json
from datetime import datetime
import paho.mqtt.client as mqtt

_running = True

def log(msg: str):
    """Print message with timestamp (YYYY-MM-DD HH:MM:SS)."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def handle_exit(signum, frame):
    """Signal handler for graceful shutdown."""
    global _running
    log("Exit signal received, shutting down...")
    _running = False

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def getenv_bool(name, default=False):
    """Read boolean from env; accepts true/false/1/0/yes/no."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}

def getenv_int(name, default):
    """Read int from env with default fallback."""
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default

def getenv_float(name, default):
    """Read float from env with default fallback."""
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default

def send(cmd_hex, ip, port, timeout):
    """Send hex command to EW11 and receive response."""
    frame = bytes.fromhex(cmd_hex)
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.sendall(frame)
            return s.recv(256)
    except (socket.timeout, TimeoutError, OSError) as e:
        log(f"Send error: {e}")
        return None

def parse_temperature(resp):
    """Parse exhaust temperature from payload (index 10)."""
    if not resp:
        return None
    p = resp[2:-2]
    data = list(p)
    if len(data) > 10:
        raw = data[10]
        return raw / 2.0 - 20
    return None

def parse_fan(resp):
    """Parse fan percentages, RPMs and active booleans from payload."""
    if not resp:
        return None, None, None, None, None, None
    p = resp[2:-2]
    data = list(p)
    if len(data) > 8:
        supply_pct  = data[5]
        extract_pct = data[6]
        supply_rpm  = round(data[7] * 20)
        extract_rpm = round(data[8] * 20)
        supply_active = (supply_pct or 0) > 0 or (supply_rpm or 0) > 0
        extract_active = (extract_pct or 0) > 0 or (extract_rpm or 0) > 0
        return supply_pct, extract_pct, supply_rpm, extract_rpm, supply_active, extract_active
    return None, None, None, None, None, None

def publish(client, topic, value):
    """Publish value to MQTT (retained)."""
    if value is None:
        return
    client.publish(topic, value, retain=True)

def publish_binary(client, topic, active):
    """Publish boolean as ON/OFF to MQTT (retained)."""
    if active is None:
        return
    state = "ON" if active else "OFF"
    client.publish(topic, state, retain=True)

def publish_discovery(client, prefix, name, manufacturer):
    """Publish Home Assistant discovery topics for sensors and binary sensors."""
    device_info = {
        "identifiers": [f"{prefix}_unit"],
        "name": name,
        "manufacturer": manufacturer,
        "model": name
    }

    sensors = [
        ("exhaust_c", f"{name} Exhaust Temp", "°C", "temperature", "sensor"),
        ("supply_pct", f"{name} Supply %", "%", "fanstatus", "sensor"),
        ("extract_pct", f"{name} Extract %", "%", "fanstatus", "sensor"),
        ("supply_rpm", f"{name} Supply RPM", "RPM", "fanstatus", "sensor"),
        ("extract_rpm", f"{name} Extract RPM", "RPM", "fanstatus", "sensor"),
        ("supply_active", f"{name} Supply Active", None, "fanstatus", "binary_sensor"),
        ("exhaust_active", f"{name} Exhaust Active", None, "fanstatus", "binary_sensor"),
    ]

    for key, sname, unit, group, entity_type in sensors:
        config = {
            "name": sname,
            "state_topic": f"{prefix}/{group}/{key}",
            "unique_id": f"{prefix}_{key}",
            "device": device_info
        }
        if unit:
            config["unit_of_measurement"] = unit
        topic = f"homeassistant/{entity_type}/{prefix}_{key}/config"
        log(f"Publishing discovery for {sname} → {topic}")
        client.publish(topic, json.dumps(config), retain=True)

def tls_version_from_env():
    """Map MQTT_TLS_VERSION env to ssl protocol."""
    ver = os.getenv("MQTT_TLS_VERSION", "").strip().upper()
    if ver == "TLSV1.2":
        return ssl.PROTOCOL_TLSv1_2
    if ver == "TLSV1.3":
        return ssl.PROTOCOL_TLS
    return ssl.PROTOCOL_TLS

def setup_mqtt_client():
    """Setup MQTT client with TLS and credentials from environment variables."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    # Authentication
    user = os.getenv("MQTT_USERNAME")
    pwd = os.getenv("MQTT_PASSWORD")
    if user and pwd:
        client.username_pw_set(user, pwd)

    # TLS configuration
    use_tls = getenv_bool("MQTT_USE_TLS", True)
    ca_cert = os.getenv("CA_CERT")
    client_cert = os.getenv("CLIENT_CERT")
    client_key = os.getenv("CLIENT_KEY")
    tls_insecure = getenv_bool("MQTT_TLS_INSECURE", False)
    tls_ver = tls_version_from_env()

    if use_tls:
        if ca_cert and client_cert and client_key:
            # Mutual TLS
            client.tls_set(ca_certs=ca_cert, certfile=client_cert, keyfile=client_key, tls_version=tls_ver)
        elif ca_cert:
            # Server-authenticated TLS
            client.tls_set(ca_certs=ca_cert, tls_version=tls_ver)
        else:
            # TLS without CA (not recommended) but supported for testing
            client.tls_set(tls_version=tls_ver)
        client.tls_insecure_set(tls_insecure)

    # Single MQTT_PORT across all modes
    broker = os.getenv("MQTT_BROKER", "localhost")
    default_port = 8883 if use_tls else 1883
    port = getenv_int("MQTT_PORT", default_port)
    keepalive = getenv_int("MQTT_KEEPALIVE", 60)

    client.reconnect_delay_set(min_delay=5, max_delay=60)
    client.connect(broker, port, keepalive)
    return client

def main():
    EW11_IP = os.getenv("EW11_IP")
    if not EW11_IP:
        log("EW11_IP is not set. Please provide EW11_IP environment variable.")
        return
    EW11_PORT = getenv_int("EW11_PORT", 502)
    SOCKET_TIMEOUT = getenv_float("SOCKET_TIMEOUT", 2.0)

    MQTT_PREFIX = os.getenv("MQTT_PREFIX", "whr90")
    NAME = os.getenv("NAME", "WHR90")
    MANUFACTURER = os.getenv("MANUFACTURER", "J.E. Storkair")

    # Commands
    CMD_TEMP = "07 F0 00 85 00 32 07 0F"
    CMD_FAN  = "07 F0 00 87 00 34 07 0F"

    client = setup_mqtt_client()
    client.loop_start()
    publish_discovery(client, MQTT_PREFIX, NAME, MANUFACTURER)

    try:
        while _running:
            try:
                t_resp = send(CMD_TEMP, EW11_IP, EW11_PORT, SOCKET_TIMEOUT)
                f_resp = send(CMD_FAN, EW11_IP, EW11_PORT, SOCKET_TIMEOUT)

                exhaust_c = parse_temperature(t_resp)
                supply_pct, extract_pct, supply_rpm, extract_rpm, supply_active, extract_active = parse_fan(f_resp)

                publish(client, f"{MQTT_PREFIX}/temperature/exhaust_c", round(exhaust_c, 1) if exhaust_c is not None else None)
                publish(client, f"{MQTT_PREFIX}/fanstatus/supply_pct", supply_pct)
                publish(client, f"{MQTT_PREFIX}/fanstatus/extract_pct", extract_pct)
                publish(client, f"{MQTT_PREFIX}/fanstatus/supply_rpm", supply_rpm)
                publish(client, f"{MQTT_PREFIX}/fanstatus/extract_rpm", extract_rpm)

                publish_binary(client, f"{MQTT_PREFIX}/fanstatus/supply_active", supply_active)
                publish_binary(client, f"{MQTT_PREFIX}/fanstatus/exhaust_active", extract_active)

                exhaust_str = f"{exhaust_c:.1f}" if exhaust_c is not None else "-"
                log(
                    f"Exhaust={exhaust_str}°C | "
                    f"sup%={supply_pct or '-'} ext%={extract_pct or '-'} | "
                    f"supRPM={supply_rpm or '-'} extRPM={extract_rpm or '-'} | "
                    f"supActive={supply_active} extActive={extract_active}"
                )

            except Exception as e:
                log(f"Communication error: {e}. Retry in 5s...")
                time.sleep(5)
                continue

            time.sleep(getenv_int("POLL_INTERVAL_SEC", 5))
    finally:
        client.loop_stop()
        client.disconnect()
        log("Shutdown complete.")

if __name__ == "__main__":
    main()
