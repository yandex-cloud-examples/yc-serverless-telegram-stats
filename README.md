Текст ниже описывает, как развернуть serverless-приложение, собирающее статистику диалогов
в группах Telegram в clickhouse в двух моделях. Развернутое приложение доливает статистику непрерывано. 

# Пререквизиты
1. Консольный [клиент clickhouse](https://clickhouse.com/docs/en/interfaces/cli)
2. Консольный [клиент Yandex Cloud](https://cloud.yandex.com/en-ru/docs/cli/quickstart)
3. Python 3.11 на ноутбуке
4. terraform v1.3.0 или выше на ноутбуке

_Если вы испытываете проблемы с установкой или использованием terraform - изучите [инструкцию](https://cloud.yandex.ru/docs/tutorials/infrastructure-management/terraform-quickstart) в документации Яндекс Облака._

_Все переменные terraform можно передавать в явном виде, либо заранее определять переменные вида `TF_VAR_<NAME>`, где NAME - имя переменной_

# Notes
Здесь показано использование CH с публичным доступом. При наличии на облаке [флага](https://cloud.yandex.ru/docs/functions/concepts/networking#polzovatelskaya-set) для запуска функций в VPC - можно все провернуть без публичного доступа, но мы сталкиваемся с ограничениями tf для функций.
В итоге можно развернуть функцию tf-рецептом, а потом воткнуть ее в VPC уже через web ui.

В этом рецепте предполагается, что все действие происходит в одном фолдере - в том же самом, в котором развернут кликхаус. Это не какое-то принципиальное ограничение, просто так проще писать рецепт.

# Генерируем секреты
1. Устанавливаем питонячьи зависимости на ноут: `pip install -r ./src/requirements.txt`
2. Создаем telegram app по [инструкции](https://core.telegram.org/api/obtaining_api_id#obtaining-api-id) - нам нужны api_id и api_hash
3. Запускаем скрипт с генерацией всех секретов: `python3 secrets/create_secrets.py --yc-folder-id <ID фолдера>`. Теперь api_id, api_hash, сессия telegram, пароль от clickhouse и ключ для вебхука telegram хранятся в секретах lockbox. В явном виде доставать их можно через UI или консольный клиент Yandex Cloud. На этом этапе клиент телеги пытается в ней авторизоваться. Он интерактивно попросит все, что ему нужно - номер телефона (вводить через +7 для рф), код подтверждения, пароль (если настроена 2fa).
4. Регистрируем telegram бота по [инструкции](https://core.telegram.org/bots/tutorial)
5. Помещаем токен бота в переменную окружения `TG_BOT_API_TOKEN`
 
# Выбираем чаты
1. Выбираем группы, для которых хотим собирать статистику. Для этого запускаем скрипт: `python3 src/list_groups.py --tg-secret-id <TG SECRET ID>` (ID секрета telegram используем с предыдущих шагов)
2. Определяем `DIALOG_IDS` - чаты, с которых можно собирать статистику: `export DIALOG_IDS=<CHAT_ID_0>,<CHAT_ID_1>,<CHAT_ID_2>,...`

# Создаем БД в кластере CH (директория clickhouse)
1. Инициализируем terraform: `terraform init`
2. Применяем спецификацию: `terraform apply -var "folder_id=<ID фолдера>"` 
3. Определяем переменные окружения `TF_VAR_CH_HOST`, `TF_VAR_CH_USER_NAME`, `TF_VAR_CH_DB_NAME`, `TF_VAR_CH_PASSWORD`
4. Создаём нужные таблицы: `./create_tables.sh`
5. Проверяем, что таблицы создались: `./select_message_count.sh` 

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
