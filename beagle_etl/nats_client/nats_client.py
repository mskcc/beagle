import ssl
import json
import signal
import logging
import asyncio
from django.conf import settings
from beagle_etl.tasks import TYPES
from beagle_etl.models import Job, JobStatus
from nats.aio.client import Client as NATS


logger = logging.getLogger(__name__)


async def run(loop):
    nc = NATS()

    async def error_cb(e):
        logger.error("Error:", e)

    async def closed_cb():
        logger.info("Connection to NATS is closed.")
        await asyncio.sleep(0.1, loop=loop)
        loop.stop()

    async def reconnected_cb():
        logger.info(f"Connected to NATS at {nc.connected_url.netloc}...")

    async def subscribe_handler(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        request_data = json.loads(data)

        logger.info("Received a message on '{subject} {reply}': {data}".format(
          subject=subject, reply=reply, data=data))
        job = Job(run=TYPES['PARSE_NEW_REQUEST'], args={'request': request_data},
                  status=JobStatus.CREATED,
                  max_retry=3, children=[])
        job.save()

    ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(certfile=settings.NATS_SSL_CERTFILE,
                            keyfile=settings.NATS_SSL_KEYFILE)

    options = {
        "loop": loop,
        "error_cb": error_cb,
        "closed_cb": closed_cb,
        "reconnected_cb": reconnected_cb,
        "servers": settings.METADB_NATS_URL,
        "username": settings.METADB_USERNAME,
        "password": settings.METADB_PASSWORD,
        "tls": ssl_ctx
    }

    try:
        await nc.connect(**options)
    except Exception as e:
        logger.error(e)

    logger.info(f"Connected to NATS at {nc.connected_url.netloc}...")

    def signal_handler():
        if nc.is_closed:
            return
        logger.info("Disconnecting...")
        loop.create_task(nc.close())

    for sig in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, sig), signal_handler)

    await nc.subscribe(settings.METADB_NATS_SUBJECT, "", subscribe_handler)
