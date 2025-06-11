This article describes how to deploy a serverless app that collects chat statistics from Telegram groups and delivers them to ClickHouse, in two models.
Once deployed, the app refreshes the statistics in real time. 

# Prerequisites
1. [Yandex Cloud console client](https://cloud.yandex.com/docs/cli/quickstart)
2. Python 3.11
3. Terraform v1.3.0 or higher

_If facing any issues in installing or using Terraform, refer to [this guide](https://yandex.cloud/docs/tutorials/infrastructure-management/terraform-quickstart) in the Yandex Cloud documentation._

_Downloading Terraform directly_

```
wget "https://hashicorp-releases.yandexcloud.net/terraform/1.5.1/terraform_1.5.1_linux_amd64.zip"
unzip terraform_1.5.1_linux_amd64.zip
sudo mv ~/terraform /usr/local/bin/
```

Once downloaded, configure the tool [as specified](https://yandex.cloud/docs/tutorials/infrastructure-management/terraform-quickstart#configure-provider).

_You can explicitly provide all Terraform variables, or define variables like `TF_VAR_<NAME>` (where `NAME` is the variable name) in advance._

# Notes
This example shows how you can use CH with public access. Where the cloud has a [flag](https://yandex.cloud/docs/functions/concepts/networking#polzovatelskaya-set) to run functions inside a VPC, you do not need public access at all; however, there are TF-specific restrictions for functions.
You can still define your function using a TF template, and then deliver it into a VPC via WebUI.

This template assumes that all actions are performed in a single folder, the same one where the ClickHouse instance is deployed. This is not a fundamental restriction; however, it is easier to write a template this way.

All sensitive data to input to scripts or Terraform will be provided through environment variables. To avoid writing them to the command line history, you can set them like this: ` export SENSITIVE_VAR=value` (the leading space is essential).

# Generate secrets and setting variables
1. Install the Python dependencies: `pip install -r ./src/requirements.txt`.
2. Create a Telegram App as per [this guide](https://core.telegram.org/api/obtaining_api_id#obtaining-api-id). You will need `api_id` and `api_hash`: assign their values to the`TG_API_ID` and `TG_API_HASH` variables.
3. Assign the OAuth token value to the `YC_TOKEN` environment variable. See how to get an OAuth token [here](https://yandex.cloud/docs/iam/concepts/authorization/oauth-token).
4. Run the script to generate all secrets: `python3 secrets/create_secrets.py --yc-folder-id <folder ID>`. Now, `api_id`, `api_hash`, the Telegram session, ClickHouse password, and Telegram webhook key are all stored in the `lockbox` secrets. You can get their values through the UI or the Yandex Cloud console client. At this step, the Telegram client tries to get authorized by the server, prompting you to provide everything it needs: phone number (specify it with the country code), confirmation code, and password (if 2FA is enabled). To get secrets, use this script: `get_secret_payload.py`.
5. Assign the IDs of the created secrets to the `TF_VAR_CH_SECRET_ID` and `TF_VAR_TG_SECRET_ID` environment variables.
6. Assign the ClickHouse password as value to the `export TF_VAR_CH_PASSWORD=$(python3 secrets/get_lockbox_payload.py --secret-id $TF_VAR_CH_SECRET_ID --key ch_cluster_password)` environment variable.
7. Register your Telegram bot as per [this guide](https://core.telegram.org/bots/tutorial).
8. Assign the bot token as value to the `TG_BOT_API_TOKEN` environment variable.
9. Set the environment variable containing a webhook key for our Telegram bot: `export TG_WEBHOOK_KEY=$(python3 secrets/get_lockbox_payload.py --secret-id $TF_VAR_TG_SECRET_ID --key tg-webhook-key)`. 

# Select the chats to monitor
1. Select the groups to collect statistics for. To do this, run this script: `python3 src/list_groups.py --tg-secret-id $TF_VAR_TG_SECRET_ID`.
2. Define `TF_VAR_DIALOG_IDS`, providing comma-separated IDs of chats to collect the statistics for: `export TF_VAR_DIALOG_IDS=<CHAT_ID_0>,<CHAT_ID_1>,<CHAT_ID_2>,...`.

# Create a database in the CH cluster (ClickHouse directory)
1. Initialize Terraform: `terraform init`
2. Apply the specification: `terraform apply -var "folder_id=<folder ID>"`. 
3. Define the environment variables: `TF_VAR_CH_HOST`, `TF_VAR_CH_USER_NAME`, and `TF_VAR_CH_DB_NAME`.
4. Create the required tables: `./create_tables.sh`.
5. Check that the tables now exist: `./select_message_count.sh`. This should return `0` (i.e., count of entries in the table where messages will be stored).

# Connect DataLens to ClickHouse
1. In DataLens Marketplace, select the [project template](http://datalens.yandex.ru/marketplace/f2ee0o8n467tk2avv39n), and click **Deploy**. 
2. Under **Connections**, enter the host name, username, and ClickHouse password from previous steps. Save the changes.
3. Now, the respective dataset, charts, and dashboard with data from ClickHouse are available.

# Deploy the `pull` model (in the `pull` directory).
1. Initialize Terraform (`terraform init`).
2. Apply the specification: `terraform apply -var "folder_id=<folder ID>"`.

# Deploy the `push` model (in the `push` directory).
1. Initialize Terraform (`terraform init`).
2. Apply the specification: `terraform apply -var "folder_id=<folder ID>"`.
3. Define the `APIGW_URL` environment variable with the value you got at the previous step.
4. Subscribe to your webhook: `./set_webhook.sh`.
