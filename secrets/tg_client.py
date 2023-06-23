import getpass
import typing

from telethon import TelegramClient
from telethon.client import AccountMethods, AuthMethods, DownloadMethods, DialogMethods, ChatMethods, UpdateMethods, BotMethods, MessageParseMethods, UserMethods, MessageMethods, UploadMethods, \
    ButtonMethods, TelegramBaseClient


class AuthMethodsWithPhone(AuthMethods):
    def start(
            self: 'AuthMethodsWithPhone',
            phone: typing.Callable[[], str] = lambda: input('Please enter your phone (or bot token): '),
            password: typing.Callable[[], str] = lambda: getpass.getpass('Please enter your password: '),
            *,
            bot_token: str = None,
            force_sms: bool = False,
            code_callback: typing.Callable[[], typing.Union[str, int]] = None,
            first_name: str = 'New User',
            last_name: str = '',
            max_attempts: int = 3) -> 'TelegramClient':
        return super(AuthMethodsWithPhone, self).start(
            lambda: getpass.getpass('Please enter your phone (or bot token): '),
            password,
            bot_token=bot_token,
            force_sms=force_sms,
            code_callback=code_callback,
            first_name=first_name,
            last_name=last_name,
            max_attempts=max_attempts,
        )


class TelegramClientWithHiddenPhone(
    AccountMethods, AuthMethodsWithPhone, DownloadMethods, DialogMethods, ChatMethods,
    BotMethods, MessageMethods, UploadMethods, ButtonMethods, UpdateMethods,
    MessageParseMethods, UserMethods, TelegramBaseClient
):
    pass
