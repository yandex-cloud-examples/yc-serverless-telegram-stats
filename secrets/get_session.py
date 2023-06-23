import getpass

from telethon.sessions import StringSession
from tg_client import TelegramClientWithHiddenPhone


def get_session(api_id, api_hash):
    with TelegramClientWithHiddenPhone(session=StringSession(), api_id=api_id, api_hash=api_hash, request_retries=10) as client:
        return client.session.save()


def main():
    tg_api_id = getpass.getpass('tg_api_id: ')
    tg_api_hash = getpass.getpass('tg_api_hash: ')

    print(get_session(tg_api_id, tg_api_hash))


if __name__ == '__main__':
    main()
