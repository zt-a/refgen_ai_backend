from celery import Celery
import src.tasks

celery_app = Celery(
    "worker",
    broker="amqp://guest:guest@localhost:5672//",
    backend="rpc://",
    include=["src.tasks.essay"]
)

celery_app.conf.task_routes = {
    "tasks.*": {"queue": "refagent"},
}

celery_app.conf.task_default_queue = "refagent"
celery_app.conf.task_default_exchange = "refagent"
celery_app.conf.task_default_routing_key = "refagent"
celery_app.conf.task_default_exchange_type = "direct"
celery_app.conf.task_default_priority = 1
