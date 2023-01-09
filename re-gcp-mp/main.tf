terraform {
  required_providers {
    rediscloud = {
      source = "RedisLabs/rediscloud"
    }
  }
}

locals {
  envs = { for tuple in regexall("(.*)=(.*)", file("env")) : tuple[0] => tuple[1] }
}

provider "rediscloud" {
  api_key    = local.envs["REDISCLOUD_ACCESS_KEY"]
  secret_key = local.envs["REDISCLOUD_SECRET_KEY"]
}

resource "rediscloud_subscription" "mc-example" {
  name           = local.envs["REDIS_SUBSCRIPTION_NAME"]
  memory_storage = "ram"
  payment_method = "marketplace"

  cloud_provider {
    provider         = "GCP"
    cloud_account_id = 1

    region {
      region                       = local.envs["GCP_REGION"]
      networking_deployment_cidr   = local.envs["REDIS_SUBSCRIPTION_CIDR"]
      preferred_availability_zones = []
    }
  }

  creation_plan {
    average_item_size_in_bytes   = 1
    memory_limit_in_gb           = 1
    quantity                     = 1
    replication                  = false
    support_oss_cluster_api      = false
    throughput_measurement_by    = "operations-per-second"
    throughput_measurement_value = 25000
    modules                      = []
  }
}

resource "rediscloud_subscription_database" "mc-example" {
  subscription_id              = rediscloud_subscription.mc-example.id
  name                         = "online-store"
  protocol                     = "redis"
  memory_limit_in_gb           = 1
  replication                  = true
  data_persistence             = "aof-every-1-second"
  throughput_measurement_by    = "operations-per-second"
  throughput_measurement_value = 25000
  average_item_size_in_bytes   = 0
  depends_on                   = [rediscloud_subscription.mc-example]
}

