curl -F "url=$APIGW_URL" -F "secret_token=$TG_WEBHOOK_KEY" "https://api.telegram.org/bot$TG_BOT_API_TOKEN/setWebhook"

