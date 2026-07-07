# Private bucket for raw uploaded documents (path convention
# raw/{workspace_id}, enforced by app code, not the bucket itself). No public
# IAM binding is added anywhere -- private by construction.
resource "google_storage_bucket" "raw_documents" {
  name                        = "${var.project_id}-${var.project_name}-raw-documents"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true

  depends_on = [google_project_service.services]
}

# Scoped to exactly this bucket -- not roles/storage.admin at the project level.
resource "google_storage_bucket_iam_member" "backend_sa_object_admin" {
  bucket = google_storage_bucket.raw_documents.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend_sa.email}"
}
