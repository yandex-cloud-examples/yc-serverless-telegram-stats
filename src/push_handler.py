import datetime
import json
import os
from collections import defaultdict

from ch_data_writer import CHDataWriter


def run(event, context):
    dialog_ids_str = os.environ.get('DIALOG_IDS')
    dialog_ids = set([int(dialog_id) for dialog_id in dialog_ids_str.split(',')])

    ch_writer = CHDataWriter(
        hostname=os.environ.get('CH_HOST'),
        login=os.environ.get('CH_USER'),
        password=os.environ.get('CH_PASS'),
        database=os.environ.get('CH_DB'),
        ca_cert=os.environ.get('CH_CA_CERT_PATH'),
    )

    data_by_chat_title = defaultdict(list)

    for message in event['messages']:
        telegram_update = json.loads(message['details']['message']['body'])
        telegram_message = telegram_update['message']
        if not telegram_message.get('text') or telegram_message.get('chat', {}).get('type') != 'group':
            continue

        group_id = abs(telegram_message['chat']['id'])
        if group_id not in dialog_ids:
            continue

        message_id = telegram_message['message_id']
        dt = datetime.datetime.fromtimestamp(telegram_message['date'])
        user_id = telegram_message['from']['id']
        message_text = telegram_message['text']
        is_forwarded = 'forward_from' in telegram_message
        reply_to_message = telegram_message.get('reply_to_message', {}).get('message_id', 0)
        topic = reply_to_message if telegram_message.get('is_topic_message') else 0
        chat_title = telegram_message['chat']['title']

        data_by_chat_title[chat_title].append([group_id, message_id, dt, user_id, message_text, is_forwarded, reply_to_message, topic])

    for group_name, data in data_by_chat_title.items():
        ch_writer.flush_messages(group_name, data)

    return {
        'statusCode': 200
    }
