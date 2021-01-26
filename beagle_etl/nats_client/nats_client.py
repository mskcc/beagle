import json
import signal
import asyncio
from nats.aio.client import Client as NATS
from beagle_etl.tasks import TYPES
from beagle_etl.models import Job, JobStatus

async def run(loop):
    nc = NATS()

    async def error_cb(e):
        print("Error:", e)

    async def closed_cb():
        print("Connection to NATS is closed.")
        await asyncio.sleep(0.1, loop=loop)
        loop.stop()

    async def reconnected_cb():
        print(f"Connected to NATS at {nc.connected_url.netloc}...")

    async def subscribe_handler(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        request_data = json.loads(data)
        print("Received a message on '{subject} {reply}': {data}".format(
          subject=subject, reply=reply, data=data))
        job = Job(run=TYPES['PARSE_NEW_REQUEST'], args={'request': request_data},
                  status=JobStatus.CREATED,
                  max_retry=3, children=[])
        job.save()

    options = {
        "loop": loop,
        "error_cb": error_cb,
        "closed_cb": closed_cb,
        "reconnected_cb": reconnected_cb
    }

    try:
        options['servers'] = "nats://127.0.0.1:4222"
        await nc.connect(**options)
    except Exception as e:
        print(e)

    print(f"Connected to NATS at {nc.connected_url.netloc}...")

    def signal_handler():
        if nc.is_closed:
            return
        print("Disconnecting...")
        loop.create_task(nc.close())

    for sig in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, sig), signal_handler)

    await nc.subscribe('NEW_REQUEST', "", subscribe_handler)
