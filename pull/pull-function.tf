terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 1.0"
}

provider "yandex" {
  folder_id = var.folder_id
}

data "archive_file" "tg-pull-func_src" {
  output_path = "${path.module}/dist/src.zip"
  type        = "zip"
  source_dir  = "${path.module}/../src"
}

resource "yandex_iam_service_account" "tg-pull-func_function" {
  name = "tg-pull-function"
}

resource "yandex_resourcemanager_folder_iam_member" "tg-pull-func_loader_read_secrets" {
  folder_id = var.folder_id
  role      = "lockbox.payloadViewer"
  member    = "serviceAccount:${yandex_iam_service_account.tg-pull-func_function.id}"
}

resource "yandex_function" "tg-pull-func" {
  entrypoint         = "pull_handler.run"
  memory             = 512
  name               = "tg-pull-func"
  runtime            = "python311"
  user_hash          = data.archive_file.tg-pull-func_src.output_base64sha256
  execution_timeout  = 300
  service_account_id = yandex_iam_service_account.tg-pull-func_function.id
  content {
    zip_filename = data.archive_file.tg-pull-func_src.output_path
  }
  environment = {
    CH_CA_CERT_PATH = "/usr/local/share/ca-certificates/yandex-internal-ca.crt"
    CH_HOST         = var.CH_HOST
    CH_DB           = var.CH_DB_NAME
    DIALOG_IDS      = var.DIALOG_IDS
    CH_USER         = var.CH_USER_NAME
  }
  secrets {
    id                   = data.yandex_lockbox_secret.tg_secret.id
    version_id           = data.yandex_lockbox_secret.tg_secret.current_version[0].id
    key                  = "api-id"
    environment_variable = "API_ID"
  }
  secrets {
    id                   = data.yandex_lockbox_secret.tg_secret.id
    version_id           = data.yandex_lockbox_secret.tg_secret.current_version[0].id
    key                  = "api-hash"
    environment_variable = "API_HASH"
  }
  secrets {
    id                   = data.yandex_lockbox_secret.tg_secret.id
    version_id           = data.yandex_lockbox_secret.tg_secret.current_version[0].id
    key                  = "session"
    environment_variable = "SESSION_STR"
  }
  secrets {
    id                   = data.yandex_lockbox_secret.ch_secret.id
    version_id           = data.yandex_lockbox_secret.ch_secret.current_version[0].id
    key                  = "ch_cluster_password"
    environment_variable = "CH_PASS"
  }
  depends_on = [
    yandex_resourcemanager_folder_iam_member.tg-pull-func_loader_read_secrets,
    data.yandex_lockbox_secret.tg_secret,
  ]
}

resource "yandex_iam_service_account" "tg-pull-func_trigger" {
  folder_id = var.folder_id
  name = "tg-pull-trigger"
}

resource "yandex_function_iam_binding" "tg-pull-func_trigger_invoke_function" {
  function_id = yandex_function.tg-pull-func.id
  members     = ["serviceAccount:${yandex_iam_service_account.tg-pull-func_trigger.id}"]
  role        = "serverless.functions.invoker"
}

resource "yandex_function_trigger" "tg-pull-func" {
  folder_id = var.folder_id
  name = "tg-pull"
  function {
    id                 = yandex_function.tg-pull-func.id
    service_account_id = yandex_iam_service_account.tg-pull-func_trigger.id
  }
  timer {
    cron_expression = "*/5 * ? * * *"
  }
  depends_on = [yandex_function_iam_binding.tg-pull-func_trigger_invoke_function]
}

variable "DIALOG_IDS" {
  type = string
}

variable "folder_id" {
  type = string
}

variable "CH_PASSWORD" {
  type = string
  sensitive = true
}

variable "CH_HOST" {
  type = string
}

variable "CH_USER_NAME" {
  type = string
  sensitive = true
  default = "ch_user"
}

variable "CH_DB_NAME" {
  type = string
  sensitive = true
  default = "tg"
}
