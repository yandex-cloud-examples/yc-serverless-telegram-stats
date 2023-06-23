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

variable "folder_id" {
  type = string
}

variable "db-name" {
  type = string
  default = "tg"
}

variable "ch-user-name" {
  type = string
  default = "ch_user"
}

resource "yandex_iam_service_account" "ch-sa" {
  name        = "ch-sa"
  description = "service account for ch cluster"
}

resource "yandex_mdb_clickhouse_cluster" "ch-stat-cluster" {
  name        = "webinar-serverless-datalens-telegram"
  environment = "PRODUCTION"
  network_id  = yandex_vpc_network.ch-stat-cluster.id

  clickhouse {
    resources {
      resource_preset_id = "s2.micro"
      disk_type_id       = "network-ssd"
      disk_size          = 32
    }

  }

  access {
    data_lens = true
  }

  database {
    name = var.db-name
  }

  user {
    name     = var.ch-user-name
    password = var.CH_PASSWORD

    permission {
      database_name = "tg"
    }
  }

  host {
    type      = "CLICKHOUSE"
    zone      = "ru-central1-a"
    subnet_id = yandex_vpc_subnet.ch-stat-cluster.id
    assign_public_ip = true
  }

  service_account_id = yandex_iam_service_account.ch-sa.id

  cloud_storage {
    enabled = false
  }

  maintenance_window {
    type = "ANYTIME"
  }

}

variable "CH_PASSWORD" {
  type = string
  sensitive = true
}

resource "yandex_vpc_network" "ch-stat-cluster" {}

resource "yandex_vpc_subnet" "ch-stat-cluster" {
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.ch-stat-cluster.id
  v4_cidr_blocks = ["10.5.0.0/24"]
}

output "ch_host" {
  value = yandex_mdb_clickhouse_cluster.ch-stat-cluster.host[0].fqdn
}

output "ch_user_name" {
  value = var.ch-user-name
}

output "ch_db_name" {
  value = var.db-name
}
