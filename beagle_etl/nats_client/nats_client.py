import ssl
import nats
import json
import signal
import logging
import asyncio
from time import sleep
from django.conf import settings
from beagle_etl.jobs.metadb_jobs import new_request, update_request_job, update_sample_job


logger = logging.getLogger(__name__)


async def run(loop, queue):

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

    for sig in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, sig), signal_handler)

    async def subscribe_handler(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        request_data = json.loads(data)

        logger.info("Received a message on '{subject} {reply}': {data}".format(
          subject=subject, reply=reply, data=data))
        if queue == settings.METADB_NATS_NEW_REQUEST:
            logger.info("Sending request: %s to new_request function" % request_data['requestId'])
            new_request.delay(request_data)
        elif queue == settings.METADB_NATS_REQUEST_UPDATE:
            logger.info("Sending request: %s to update_request_job function" % request_data['requestId'])
            update_request_job.delay(request_data)
        elif queue == settings.METADB_NATS_SAMPLE_UPDATE:
            logger.info("Sending request: %s to update_sample_job function" % request_data['requestId'])
            update_sample_job.delay(request_data)

    ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(certfile=settings.NATS_SSL_CERTFILE,
                            keyfile=settings.NATS_SSL_KEYFILE)

    options = {
        "error_cb": error_cb,
        "closed_cb": closed_cb,
        "reconnected_cb": reconnected_cb,
        "servers": settings.METADB_NATS_URL,
        "user": settings.METADB_USERNAME,
        "password": settings.METADB_PASSWORD,
        "tls": ssl_ctx
    }

    nc = await nats.connect(**options)

    try:
        js = nc.jetstream()
        sub = await js.subscribe(queue, durable="durable",
                                 config={'filter_subject': settings.METADB_NATS_FILTER_SUBJECT})
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
