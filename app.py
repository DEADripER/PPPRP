import json
import logging
import os
import sys
import time
from threading import Lock
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest


CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "/app/config/config.json"))
DEFAULT_CONFIG = {
    "welcome_message": "Welcome to the custom app",
    "log_level": "INFO",
    "log_file": "/app/logs/app.log",
    "port": 8080,
}
POD_NAME = os.getenv("POD_NAME", os.getenv("HOSTNAME", "unknown-pod"))

app = Flask(__name__)
logger = logging.getLogger("custom-app")

LOG_REQUESTS_TOTAL = Counter(
    "custom_app_log_requests_total",
    "Total number of POST /log calls.",
)
LOG_ATTEMPTS_TOTAL = Counter(
    "custom_app_log_attempts_total",
    "POST /log logging attempts by result.",
    ["result"],
)
LOG_REQUEST_DURATION_SECONDS = Histogram(
    "custom_app_log_request_duration_seconds",
    "Time spent processing POST /log requests.",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
LOG_REQUEST_DURATION_AVERAGE_SECONDS = Gauge(
    "custom_app_log_request_duration_seconds_average",
    "Average time spent processing POST /log requests.",
)
_duration_lock = Lock()
_duration_total_seconds = 0.0
_duration_count = 0


def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        if isinstance(data, dict):
            config.update(data)
    return config


def ensure_log_file(log_file: str) -> Path:
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


class PodNameFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.pod_name = POD_NAME
        return True


def setup_logger(config: dict) -> logging.Logger:
    level = getattr(logging, str(config.get("log_level", "INFO")).upper(), logging.INFO)
    log_file = ensure_log_file(str(config.get("log_file", DEFAULT_CONFIG["log_file"])))

    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [pod=%(pod_name)s] %(message)s"
    )
    pod_filter = PodNameFilter()

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(pod_filter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(pod_filter)
    logger.addHandler(stream_handler)

    return logger


def current_logger() -> logging.Logger:
    return setup_logger(load_config())


def record_log_metrics(result: str, duration_seconds: float) -> None:
    global _duration_count, _duration_total_seconds

    LOG_ATTEMPTS_TOTAL.labels(result=result).inc()
    LOG_REQUEST_DURATION_SECONDS.observe(duration_seconds)

    with _duration_lock:
        _duration_total_seconds += duration_seconds
        _duration_count += 1
        LOG_REQUEST_DURATION_AVERAGE_SECONDS.set(
            _duration_total_seconds / _duration_count
        )


@app.after_request
def add_pod_header(response):
    response.headers["X-Pod-Name"] = POD_NAME
    return response


@app.get("/")
def root():
    config = load_config()
    return config.get("welcome_message", DEFAULT_CONFIG["welcome_message"]), 200


@app.get("/status")
def status():
    return jsonify({"status": "ok"}), 200


@app.post("/log")
def write_log():
    started_at = time.perf_counter()
    result = "failure"
    LOG_REQUESTS_TOTAL.inc()

    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "message is required"}), 400

        message = str(data.get("message", "")).strip()
        if not message:
            return jsonify({"error": "message is required"}), 400

        current_logger().info(message)
        result = "success"
        return jsonify({"result": "logged", "pod": POD_NAME}), 200
    finally:
        record_log_metrics(result, time.perf_counter() - started_at)


@app.get("/logs")
def read_logs():
    config = load_config()
    log_file = ensure_log_file(str(config.get("log_file", DEFAULT_CONFIG["log_file"])))

    try:
        content = log_file.read_text(encoding="utf-8")
    except OSError:
        content = ""

    return Response(content, mimetype="text/plain")


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    config = load_config()
    setup_logger(config).info("Starting custom app on port %s", config["port"])
    app.run(host="0.0.0.0", port=int(config["port"]))
