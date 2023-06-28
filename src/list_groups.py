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


async def list_groups(title_filter, tg_session, tg_api_id, tg_api_hash):
    print('Title filter: ', title_filter)

    count = 0
    async with TelegramClient(session=StringSession(tg_session), api_id=tg_api_id,
                              api_hash=tg_api_hash, request_retries=10) as client:

        async for dialog in client.iter_dialogs():  # type: Dialog
            if not (dialog.is_group or dialog.is_channel):
                continue

            group = dialog.entity
            if title_filter and title_filter not in group.title:
                continue

            print(f'{group.title}: {group.id}')
            count += 1
            if count % 10 == 0:
                if input('Continue? [y/n]') != 'y':
                    break


async def list_groups_main() -> None:
    flag_parser = argparse.ArgumentParser()

    flag_parser.add_argument("--tg-secret-id", type=str, required=True)
    flag_parser.add_argument("--title-filter", type=str)

    args = flag_parser.parse_args()

    tg_session = os.getenv('TG_SESSION')
    tg_api_id = os.getenv('TG_API_ID')
    tg_api_hash = os.getenv('TG_API_HASH')
    if tg_session and tg_api_id and tg_api_hash:
        await list_groups(args.title_filter, tg_session, tg_api_id, tg_api_hash)
        return

    yc_token = os.getenv('YC_TOKEN')
    if not yc_token:
        yc_token = getpass.getpass('YC_TOKEN: ')

    yc_sdk = yandexcloud.SDK(token=yc_token)

    lb_client: PayloadServiceStub = yc_sdk.client(PayloadServiceStub)
    secret: Payload = lb_client.Get(GetPayloadRequest(
        secret_id=args.tg_secret_id
    ))
    secret_dict = {entry.key: entry.text_value for entry in secret.entries}

    await list_groups(args.title_filter, secret_dict['session'], secret_dict['api-id'], secret_dict['api-hash'])


if __name__ == '__main__':
    asyncio.run(
        list_groups_main()
    )
