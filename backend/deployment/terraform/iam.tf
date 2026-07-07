# Backend service account -- granted only the project-level roles it needs
# (Firestore, Vertex AI, logging). GCS access is scoped separately, per
# bucket, in storage.tf -- no project-wide storage role.
resource "google_service_account" "backend_sa" {
  account_id   = "${var.project_name}-app"
  display_name = "${var.project_name} Cloud Run Service Account"
  project      = var.project_id
  depends_on   = [google_project_service.services]
}

resource "google_project_iam_member" "backend_sa_roles" {
  for_each = toset(var.app_sa_roles)

  project    = var.project_id
  role       = each.value
  member     = "serviceAccount:${google_service_account.backend_sa.email}"
  depends_on = [google_project_service.services]
}
