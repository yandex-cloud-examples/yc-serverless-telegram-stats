import os

tg_webhook_key = os.getenv('TG_WEBHOOK_KEY')


def run(event, context):
    is_authorized = tg_webhook_key == event['headers'].get('X-Telegram-Bot-Api-Secret-Token')
    print(event, is_authorized)

    return {
        'isAuthorized': is_authorized
    }
