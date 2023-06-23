resource "yandex_message_queue" "push-ymq" {
  depends_on = [
    yandex_iam_service_account_static_access_key.ymq-static-key,
    yandex_resourcemanager_folder_iam_member.folder-editor,
  ]
  name = "push-ymq"

  access_key = yandex_iam_service_account_static_access_key.ymq-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.ymq-static-key.secret_key
}

resource "yandex_iam_service_account_static_access_key" "ymq-static-key" {
  service_account_id = yandex_iam_service_account.folder-editor.id
  description        = "static access key for sqs"
}

resource "yandex_iam_service_account" "func-invoker" {
  name = "func-invoker"
}

resource "yandex_resourcemanager_folder_iam_member" "func-invoker" {
  folder_id = var.folder_id
  member    = "serviceAccount:${yandex_iam_service_account.func-invoker.id}"
  role      = "serverless.functions.invoker"
}

resource "yandex_iam_service_account" "folder-editor" {
  name = "folder-editor"
}

resource "yandex_resourcemanager_folder_iam_member" "folder-editor" {
  folder_id = var.folder_id
  member    = "serviceAccount:${yandex_iam_service_account.folder-editor.id}"
  role      = "editor"
}

resource "yandex_function_trigger" push-trigger {
  folder_id = var.folder_id
  name      = "push-trigger"
  message_queue {
    queue_id = yandex_message_queue.push-ymq.arn
    batch_cutoff = 1
    batch_size = 10
    service_account_id = yandex_iam_service_account.folder-editor.id
  }
  function {
    id                 = yandex_function.tg-push-func.id
    service_account_id = yandex_iam_service_account.func-invoker.id
  }
}
