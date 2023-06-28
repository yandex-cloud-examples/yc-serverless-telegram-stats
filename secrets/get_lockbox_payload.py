import argparse

import yandexcloud
from yandex.cloud.lockbox.v1.payload_service_pb2 import GetPayloadRequest
from yandex.cloud.lockbox.v1.payload_service_pb2_grpc import PayloadServiceStub

from util import getenv_or_error


def main():
    flag_parser = argparse.ArgumentParser()
    flag_parser.add_argument("--secret-id", type=str, required=True)
    flag_parser.add_argument("--key", type=str, required=True)
    args = flag_parser.parse_args()

    yc_token = getenv_or_error('YC_TOKEN')
    yc_sdk = yandexcloud.SDK(token=yc_token)

    client: PayloadServiceStub = yc_sdk.client(PayloadServiceStub)
    payload = client.Get(GetPayloadRequest(
        secret_id=args.secret_id
    ))

    entries = {entry.key: entry.text_value for entry in payload.entries}
    if args.key not in entries:
        raise ValueError(f'Can not find key {args.key} in secret {args.secret_id}')
    print(entries[args.key])


if __name__ == '__main__':
    main()
