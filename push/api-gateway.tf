resource "yandex_api_gateway" "push-api-gateway" {
  name = "push-api-gw"
  description = "Push API Gateway"
  spec = <<-EOT
openapi: 3.0.0
info:
  title: Push API
  version: 1.0.0
paths:
  /push_update:
    post:
      summary: Auth op
      operationId: ApiKeyAuth
      security:
        - ApiKeyAuth: [ ]
      x-yc-apigateway-integration:
        type: cloud_ymq
        action: SendMessage
        queue_url: ${yandex_message_queue.push-ymq.id}
        folder_id: ${var.folder_id}
        service_account_id: ${yandex_iam_service_account.ymq-sa.id}
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-Telegram-Bot-Api-Secret-Token
      x-yc-apigateway-authorizer:
        type: function
        function_id: ${yandex_function.tg-auth-func.id}
        tag: "$latest"
        service_account_id: ${yandex_iam_service_account.func-invoker.id}
        authorizer_result_ttl_in_seconds: 300
EOT
}

output "apigw-url" {
  value = "https://${yandex_api_gateway.push-api-gateway.domain}/push_update"
}
