import argparse, sys
import asyncio
import json
import os
import signal
from nats.aio.client import Client as NATS


def show_usage():
    usage = """
nats-req SUBJECT [-d DATA] [-s SERVER]
Example:
nats-req hello -d world -s nats://127.0.0.1:4222 -s nats://127.0.0.1:4223
"""
    print(usage)


def show_usage_and_die():
    show_usage()
    sys.exit(1)


async def run(loop):
    parser = argparse.ArgumentParser()

    # e.g. nats-req hello -d "world" -s nats://127.0.0.1:4222 -s nats://127.0.0.1:4223
    parser.add_argument('subject', default='hello', nargs='?')
    parser.add_argument('-d', '--data', default="hello world")
    parser.add_argument('-s', '--servers', default=[], action='append')
    parser.add_argument('--creds', default="")
    args = parser.parse_args()

    nc = NATS()

    async def error_cb(e):
        print("Error:", e)

    async def closed_cb():
        print("Connection to NATS is closed.")

    async def reconnected_cb():
        print(f"ReConnected to NATS at {nc.connected_url.netloc}...")

    options = {
        "loop": loop,
        "error_cb": error_cb,
        "closed_cb": closed_cb,
        "reconnected_cb": reconnected_cb
    }

    if len(args.creds) > 0:
        options["user_credentials"] = args.creds

    try:
        if len(args.servers) > 0:
            options['servers'] = args.servers

        await nc.connect(**options)
    except Exception as e:
        print(e)
        show_usage_and_die()

    print(f"Connected to NATS at {nc.connected_url.netloc}...")
    # msg = await nc.request(args.subject, args.data.encode())
    # subject = msg.subject
    # reply = msg.reply
    # data = msg.data.decode()
    # print("Received a message on '{subject} {reply}': {data}".format(
    #     subject=subject, reply=reply, data=data))
    with open(args.data, 'r') as f:
        data = json.load(f)
        data_str = json.dumps(data)

    await nc.publish(args.subject, data_str.encode())
    await nc.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run(loop))
    finally:
        loop.close()
