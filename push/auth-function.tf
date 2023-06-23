resource "yandex_iam_service_account" "tg-auth-func" {
  name = "tg-auth-function"
}

resource "yandex_resourcemanager_folder_iam_member" "tg_auth_read_secrets" {
  folder_id = var.folder_id
  role      = "lockbox.payloadViewer"
  member    = "serviceAccount:${yandex_iam_service_account.tg-auth-func.id}"
}

resource "yandex_function" "tg-auth-func" {
  folder_id = var.folder_id
  entrypoint         = "auth_handler.run"
  memory             = 512
  name               = "tg-auth-func"
  runtime            = "python311"
  user_hash          = data.archive_file.tg-push-func_src.output_base64sha256
  execution_timeout  = 300
  service_account_id = yandex_iam_service_account.tg-auth-func.id
  content {
    zip_filename = data.archive_file.tg-push-func_src.output_path
  }
  environment = {
    CH_CA_CERT_PATH = "/usr/local/share/ca-certificates/yandex-internal-ca.crt"
  }
  secrets {
    id                   = data.yandex_lockbox_secret.tg_secret.id
    version_id           = data.yandex_lockbox_secret.tg_secret.current_version[0].id
    key                  = "tg-webhook-key"
    environment_variable = "TG_WEBHOOK_KEY"
  }
  depends_on = [
    yandex_resourcemanager_folder_iam_member.tg_auth_read_secrets,
    data.yandex_lockbox_secret.tg_secret,
  ]
}
