output "db_public_endpoint" {
  value       = rediscloud_subscription_database.mc-example.public_endpoint
  description = "The Redis DB endpoint"
}

output "db_password" {
  value       = rediscloud_subscription_database.mc-example.password
  sensitive   = true
  description = "The Redis DB Password"
}
