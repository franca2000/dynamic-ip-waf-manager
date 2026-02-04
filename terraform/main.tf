provider "aws" {
  region = "us-east-1"
}

# 1. Container Registry (Where the Docker image is stored)
resource "aws_ecr_repository" "waf_manager_repo" {
  name                 = "waf-manager-repo"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# 2. Application Service (Serverless Container Runner)
resource "aws_apprunner_service" "waf_manager_service" {
  service_name = "waf-manager-service"

  source_configuration {
    # Reference the image from the ECR repository created above
    image_repository {
      image_identifier      = "${aws_ecr_repository.waf_manager_repo.repository_url}:latest"
      image_repository_type = "ECR"
      
      image_configuration {
        port = "8000" # The port exposed by our Dockerfile
        runtime_environment_variables = {
          "ENV" = "production"
        }
      }
    }
    
    # IAM Role required for App Runner to pull images from ECR.
    # Note: In a full implementation, this role would be created via an aws_iam_role resource.
    # Here we use a placeholder ARN for demonstration purposes.
    authentication_configuration {
      access_role_arn = "arn:aws:iam::123456789012:role/service-role/AppRunnerECRAccessRole"
    }
  }

  instance_configuration {
    cpu    = "1024"
    memory = "2048"
  }

  tags = {
    Environment = "Production"
    Project     = "Yuno-WAF-Challenge"
  }
}

# 3. Output: The public URL provided by AWS
output "service_url" {
  value       = aws_apprunner_service.waf_manager_service.service_url
  description = "Public URL to access the WAF Manager API"
}