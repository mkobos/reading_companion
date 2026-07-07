output "cloud_run_service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "raw_documents_bucket_name" {
  description = "Name of the private GCS bucket for raw uploaded documents"
  value       = google_storage_bucket.raw_documents.name
}

output "backend_service_account_email" {
  description = "Email of the backend Cloud Run service account"
  value       = google_service_account.backend_sa.email
}
