Текст ниже описывает, как развернуть serverless-приложение, собирающее статистику диалогов
в группах Telegram в clickhouse в двух моделях. Развернутое приложение доливает статистику непрерывано. 

# Пререквизиты
1. Консольный [клиент Yandex Cloud](https://cloud.yandex.com/en-ru/docs/cli/quickstart)
2. Python 3.11
3. terraform v1.3.0 или выше

_Если вы испытываете проблемы с установкой или использованием terraform - изучите [инструкцию](https://cloud.yandex.ru/docs/tutorials/infrastructure-management/terraform-quickstart) в документации Яндекс Облака._

_Самостоятельная загрузка terraform_
```
wget "https://hashicorp-releases.yandexcloud.net/terraform/1.5.1/terraform_1.5.1_linux_amd64.zip"
unzip terraform_1.5.1_linux_amd64.zip
sudo mv ~/terraform /usr/local/bin/
```
и делаем настройки описанные [тут](https://cloud.yandex.ru/docs/tutorials/infrastructure-management/terraform-quickstart#configure-provider)

_Все переменные terraform можно передавать в явном виде, либо заранее определять переменные вида `TF_VAR_<NAME>`, где NAME - имя переменной_

# Notes
Здесь показано использование CH с публичным доступом. При наличии на облаке [флага](https://cloud.yandex.ru/docs/functions/concepts/networking#polzovatelskaya-set) для запуска функций в VPC - можно все провернуть без публичного доступа, но мы сталкиваемся с ограничениями tf для функций.
В итоге можно развернуть функцию tf-рецептом, а потом воткнуть ее в VPC уже через web ui.

В этом рецепте предполагается, что все действие происходит в одном фолдере - в том же самом, в котором развернут кликхаус. Это не какое-то принципиальное ограничение, просто так проще писать рецепт.

Все чувствительные данные, которые нужны на вход скриптам / терраформу будут прокидываться через переменные окружения, их можно выставить так (с пробелом в начале): ` export SENSITIVE_VAR=value`, чтобы не записывать их в историю командной строки.

# Генерируем секреты и выставляем переменные
1. Устанавливаем зависимости python: `pip install -r ./src/requirements.txt`
2. Создаем telegram app по [инструкции](https://core.telegram.org/api/obtaining_api_id#obtaining-api-id) - нам нужны api_id и api_hash, выставляем их значения в переменные `TG_API_ID` и `TG_API_HASH`
3. Выставляем OAuth-токен в переменную окружения `YC_TOKEN`. [Как получить OAuth токен](https://cloud.yandex.ru/docs/iam/concepts/authorization/oauth-token)
4. Запускаем скрипт с генерацией всех секретов: `python3 secrets/create_secrets.py --yc-folder-id <ID фолдера>`. Теперь api_id, api_hash, сессия telegram, пароль от clickhouse и ключ для вебхука telegram хранятся в секретах lockbox. В явном виде доставать их можно через UI или консольный клиент Yandex Cloud. На этом этапе клиент телеги пытается в ней авторизоваться. Он интерактивно попросит все, что ему нужно - номер телефона (вводить через +7 для рф), код подтверждения, пароль (если настроена 2fa). Доставать секреты можно с помощью скрипта `get_secret_payload.py`
5. Выставляем id созданных секретов в переменные окружения `TF_VAR_CH_SECRET_ID` и `TF_VAR_TG_SECRET_ID`
6. Выставляем пароль кликхауса в переменную окружения: `export TF_VAR_CH_PASSWORD=$(python3 secrets/get_lockbox_payload.py --secret-id $TF_VAR_CH_SECRET_ID --key ch_cluster_password)`
7. Регистрируем telegram бота по [инструкции](https://core.telegram.org/bots/tutorial)
8. Помещаем токен бота в переменную окружения `TG_BOT_API_TOKEN`
9. Выставляем переменную окружения с ключом для вебхука телеграм-бота: `export TG_WEBHOOK_KEY=$(python3 secrets/get_lockbox_payload.py --secret-id $TF_VAR_TG_SECRET_ID --key tg-webhook-key)` 

# Выбираем чаты
1. Выбираем группы, для которых хотим собирать статистику. Для этого запускаем скрипт: `python3 src/list_groups.py --tg-secret-id $TF_VAR_TG_SECRET_ID`
2. Определяем `TF_VAR_DIALOG_IDS` - id чатов, с которых можно собирать статистику, указанные через запятую: `export TF_VAR_DIALOG_IDS=<CHAT_ID_0>,<CHAT_ID_1>,<CHAT_ID_2>,...`

# Создаем БД в кластере CH (директория clickhouse)
1. Инициализируем terraform: `terraform init`
2. Применяем спецификацию: `terraform apply -var "folder_id=<ID фолдера>"` 
3. Определяем переменные окружения `TF_VAR_CH_HOST`, `TF_VAR_CH_USER_NAME`, `TF_VAR_CH_DB_NAME`
4. Создаём нужные таблицы: `./create_tables.sh`
5. Проверяем, что таблицы создались: `./select_message_count.sh` - должен вывестись `0`, как количество записей в таблице сообщений

# Подключаем datalens к clickhouse
1. Заходим в маркетплейс datalens, находим [шаблон проекта](http://datalens.yandex.ru/marketplace/f2ee0o8n467tk2avv39n) и нажимаем "Развернуть" 
2. Заходим в подключения и вводим имя хоста, имя пользователя и пароль к clickhouse из предыдущих шагов и сохраняем изменения
3. Теперь можно смотреть на датасет, чарты и дашборд с данными из clickhouse

# Разворачиваем модель pull (директория pull)
1. Инициализируем terraform: `terraform init`
2. Применяем спецификацию: `terraform apply -var "folder_id=<ID фолдера>"`

# Разворачиваем модель push (директория push)
1. Инициализируем terraform: `terraform init`
2. Применяем спецификацию: `terraform apply -var "folder_id=<ID фолдера>"`
3. Определяем переменную окружения `APIGW_URL` со значением из предыдущего шага
4. Подписываемся на вебхук: `./set_webhook.sh`
