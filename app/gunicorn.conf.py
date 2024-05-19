import multiprocessing
import os

name = "MyChatbotAPI"
wsgi_app = "api:app"
bind = "0.0.0.0:8000"
debug = False
reload = debug
preload_app = False
daemon = False

worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1024
backlog = 2048
max_requests = 5120
timeout = 120
keepalive = 2

loglevel = "info"
errorlog = "-"
accesslog = "-"

secure_scheme_headers = {
    "X-FORWARDED-PROTOCOL": "ssl",
    "X-FORWARDED-PROTO": "https",
    "X-FORWARDED-SSL": "on",
}
