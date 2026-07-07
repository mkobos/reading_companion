variable "project_id" {
  type        = string
  description = "Google Cloud Project ID for resource deployment."
}

variable "project_name" {
  type        = string
  description = "Project name used as a base for resource naming."
  default     = "reading-companion-backend"
}

variable "region" {
  type        = string
  description = "Google Cloud region for resource deployment."
  default     = "us-east1"
}

variable "container_image" {
  type        = string
  description = <<-EOT
    Container image for the Cloud Run service. Defaults to a public
    placeholder; a real deploy pipeline overwrites this (see service.tf's
    lifecycle.ignore_changes), so Terraform never reverts a deployed image.
  EOT
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "discussion_agent_url" {
  type        = string
  description = <<-EOT
    Base URL of the discussion-agent service. Empty by default -- discussion-agent
    has not been deployed to Vertex AI Agent Engine yet, so there is no real
    target for this Cloud Run service to call.
  EOT
  default     = ""
}

variable "allow_origins" {
  type        = string
  description = "Comma-separated list of allowed CORS origins for the frontend SPA."
  default     = ""
}

variable "app_sa_roles" {
  description = "Project-level roles granted to the backend service account."
  type        = list(string)
  default = [
    "roles/datastore.user",
    "roles/aiplatform.user",
    "roles/logging.logWriter",
  ]
}
