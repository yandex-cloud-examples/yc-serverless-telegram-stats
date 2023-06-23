data "yandex_lockbox_secret" "tg_secret" {
  secret_id = var.TG_SECRET_ID
}

data "yandex_lockbox_secret" "ch_secret" {
  secret_id = var.CH_SECRET_ID
}

variable "TG_SECRET_ID" {
  type = string
}

variable "CH_SECRET_ID" {
  type = string
}
