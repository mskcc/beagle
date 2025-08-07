import ssl
import nats
import json
import signal
import logging
import asyncio
from time import sleep
from django.conf import settings
from datetime import datetime, timezone
from nats.js.api import DeliverPolicy
from beagle_etl.models import SMILEMessage


logger = logging.getLogger(__name__)


def persist_message(topic, message):
    try:
        msg = SMILEMessage.objects.create(topic=topic, message=message)
        request_message = json.loads(message)
        if topic == settings.METADB_NATS_NEW_REQUEST:
            msg.request_id = request_message.get(settings.REQUEST_ID_METADATA_KEY)
        elif topic == settings.METADB_NATS_REQUEST_UPDATE:
            msg.request_id = request_message[0].get(settings.REQUEST_ID_METADATA_KEY)
        elif topic == settings.METADB_NATS_SAMPLE_UPDATE:
            msg.request_id = request_message["latestSampleMetadata"][settings.SAMPLE_ID_METADATA_KEY]
        msg.save()
    except Exception as e:
        logger.error(e)


async def run(loop, queue, start_time=None):
    async def error_cb(e):
        logger.error("Error:", e)

    async def closed_cb():
        logger.info("Connection to NATS is closed.")
        await asyncio.sleep(0.1, loop=loop)
        loop.stop()

    async def reconnected_cb():
        logger.info(f"Connected to NATS at {nc.connected_url}...")

    def signal_handler():
        if nc.is_closed:
            return
        logger.info("Disconnecting...")
        loop.create_task(nc.close())

    for sig in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(getattr(signal, sig), signal_handler)

    async def subscribe_handler(msg):
        subject = msg.subject
        reply = msg.reply
        data = json.loads(msg.data.decode())
        logger.info("Received a message on '{subject} {reply}': {data}".format(subject=subject, reply=reply, data=data))
        persist_message(subject, data)

    options = {
        "error_cb": error_cb,
        "closed_cb": closed_cb,
        "reconnected_cb": reconnected_cb,
        "servers": settings.METADB_NATS_URL,
        "user": settings.METADB_USERNAME,
        "password": settings.METADB_PASSWORD,
    }

    if settings.NATS_SSL_CERTFILE and settings.NATS_SSL_KEYFILE:
        ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        if settings.NATS_ROOT_CA:
            ssl_ctx.load_verify_locations(cafile=settings.NATS_ROOT_CA)
        ssl_ctx.load_cert_chain(certfile=settings.NATS_SSL_CERTFILE, keyfile=settings.NATS_SSL_KEYFILE)
        options["tls"] = ssl_ctx

    nc = await nats.connect(**options)

    try:
        config = {"filter_subject": settings.METADB_NATS_FILTER_SUBJECT}
        if start_time:
            config["deliver_policy"] = "by_start_time"
            config["opt_start_time"] = start_time
        else:
            config["deliver_policy"] = "new"
        js = nc.jetstream()
        sub = await js.subscribe(queue, durable=settings.METADB_NATS_DURABLE, config=config)
        logger.info(f"Connected to NATS at {nc.connected_url}...")
    except Exception as e:
        logger.error(e)

    while True:
        try:
            msg = await sub.next_msg(timeout=settings.METADB_CLIENT_TIMEOUT)
            await subscribe_handler(msg)
            await msg.ack()
        except Exception as e:
            sleep(1)
