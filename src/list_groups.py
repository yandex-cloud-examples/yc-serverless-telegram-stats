from __future__ import annotations

import argparse
import asyncio
import getpass
import os

import yandexcloud
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.custom.dialog import Dialog
from yandex.cloud.lockbox.v1.payload_pb2 import Payload
from yandex.cloud.lockbox.v1.payload_service_pb2 import GetPayloadRequest
from yandex.cloud.lockbox.v1.payload_service_pb2_grpc import PayloadServiceStub

flag_parser = argparse.ArgumentParser()

flag_parser.add_argument("--tg-secret-id", type=str, required=True)
flag_parser.add_argument("--title-filter", type=str)


async def list_groups() -> None:
    args = flag_parser.parse_args()
    iam_token = os.getenv('YC_TOKEN')
    if not iam_token:
        iam_token = getpass.getpass('YC_TOKEN: ')

    yc_sdk = yandexcloud.SDK(iam_token=iam_token)

    lb_client: PayloadServiceStub = yc_sdk.client(PayloadServiceStub)
    secret: Payload = lb_client.Get(GetPayloadRequest(
        secret_id=args.tg_secret_id
    ))
    secret_dict = {entry.key: entry.text_value for entry in secret.entries}

    print('Title filter: ', args.title_filter)

    count = 0
    async with TelegramClient(session=StringSession(secret_dict['session']), api_id=secret_dict['api-id'],
                              api_hash=secret_dict['api-hash'], request_retries=10) as client:

        async for dialog in client.iter_dialogs():  # type: Dialog
            if not (dialog.is_group or dialog.is_channel):
                continue

            group = dialog.entity
            if args.title_filter and args.title_filter not in group.title:
                continue

            print(f'{group.title}: {group.id}')
            count += 1
            if count % 10 == 0:
                if input('Continue? [y/n]') != 'y':
                    break


if __name__ == '__main__':
    asyncio.run(
        list_groups()
    )
