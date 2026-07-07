resource "google_cloud_run_v2_service" "backend" {
  name     = var.project_name
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend_sa.email

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.raw_documents.name
      }

      env {
        name  = "MAX_UPLOAD_SIZE_BYTES"
        value = "2000000"
      }

      env {
        name  = "RATE_LIMIT_MAX_REQUESTS"
        value = "10"
      }

      env {
        name  = "RATE_LIMIT_WINDOW_SECONDS"
        value = "60"
      }

      env {
        name  = "ALLOW_ORIGINS"
        value = var.allow_origins
      }

      # No real Agent Engine deployment exists yet -- see variables.tf. Until
      # one does, discussion endpoints will 502 (agent-contract.yaml's
      # documented AgentFailure), not a gap introduced by this file.
      env {
        name  = "DISCUSSION_AGENT_URL"
        value = var.discussion_agent_url
      }

      env {
        name  = "DISCUSSION_AGENT_TIMEOUT_SECONDS"
        value = "30"
      }

      env {
        name  = "GOOGLE_GENAI_USE_ENTERPRISE"
        value = "true"
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = "global"
      }

      env {
        name  = "SUGGESTIONS_MODEL"
        value = "gemini-flash-latest"
      }

      env {
        name  = "JOURNAL_MODEL"
        value = "gemini-flash-latest"
      }

      env {
        name  = "LLM_TIMEOUT_SECONDS"
        value = "15"
      }
    }
  }

  # A future CI/CD deploy overwrites the image and may adjust env vars;
  # Terraform must never revert that -- same rationale as
  # discussion-agent/deployment/terraform/single-project/service.tf.
  lifecycle {
    ignore_changes = [template]
  }

  depends_on = [google_project_service.services]
}

# Intentionally public: this is the app's own user-facing surface (FastAPI +,
# eventually, the built SPA), unlike the Agent Engine resource, which per
# tech-spec §8 is never exposed publicly.
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "allUsers"
}
