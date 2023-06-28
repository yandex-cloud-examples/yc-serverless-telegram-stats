import argparse
import random
import string

import yandexcloud
from yandex.cloud.lockbox.v1.secret_pb2 import Secret
from yandex.cloud.lockbox.v1.secret_service_pb2 import CreateSecretRequest, PayloadEntryChange, AddVersionRequest
from yandex.cloud.lockbox.v1.secret_service_pb2_grpc import SecretServiceStub

from get_session import get_session
from util import getenv_or_error

ALPHABET = string.ascii_letters + string.digits


def gen_string(length=25):
    return ''.join(random.choice(ALPHABET) for _ in range(length))


def create_secret(yc_sdk, folder_id, name, data):
    client: SecretServiceStub = yc_sdk.client(SecretServiceStub)
    create_secret_op = client.Create(CreateSecretRequest(
        folder_id=folder_id,
        name=name,
        version_payload_entries=[PayloadEntryChange(key=key, text_value=value) for key, value in data.items()]
    ))
    create_secret_res = yc_sdk.wait_operation_and_get_result(
        create_secret_op,
        response_type=Secret
    )
    return create_secret_res.response.id


def create_tg_secret(yc_sdk, folder_id, api_id, api_hash, session):
    return create_secret(yc_sdk, folder_id, 'tg-creds', {
        'api-id': str(api_id),
        'api-hash': api_hash,
        'session': session,
        'tg-webhook-key': gen_string(50)
    })


def create_ch_secret(yc_sdk, folder_id):
    return create_secret(yc_sdk, folder_id, 'ch_cluster_password', {'ch_cluster_password': gen_string(50)})


def add_session_to_secret(yc_sdk, secret_id, session):
    client: SecretServiceStub = yc_sdk.client(SecretServiceStub)
    update_secret_op = client.AddVersion(AddVersionRequest(
        secret_id=secret_id,
        payload_entries=[PayloadEntryChange(
            key='session',
            text_value=session
        )]
    ))
    yc_sdk.wait_operation_and_get_result(update_secret_op)


def main():
    flag_parser = argparse.ArgumentParser()
    flag_parser.add_argument("--yc-folder-id", type=str, required=True)
    args = flag_parser.parse_args()

    yc_token = getenv_or_error('YC_TOKEN')
    tg_api_id = getenv_or_error('TG_API_ID')
    tg_api_hash = getenv_or_error('TG_API_HASH')

    yc_sdk = yandexcloud.SDK(token=yc_token)
    session = get_session(tg_api_id, tg_api_hash)
    tg_secret_id = create_tg_secret(yc_sdk, args.yc_folder_id, tg_api_id, tg_api_hash, session)
    ch_secret_id = create_ch_secret(yc_sdk, args.yc_folder_id)
    print(f'Telegram secret id: {tg_secret_id}')
    print(f'Clickhouse secret id: {ch_secret_id}')


if __name__ == '__main__':
    main()
