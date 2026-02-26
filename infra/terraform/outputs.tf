output "alb_dns_name" {
  description = "Public DNS of application load balancer"
  value       = aws_lb.app.dns_name
}

output "ecr_repository_url" {
  description = "Push container images here"
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.app.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.app.name
}
