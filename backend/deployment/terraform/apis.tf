locals {
  services = [
    "run.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "aiplatform.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
  ]
}

resource "google_project_service" "services" {
  count              = length(local.services)
  project            = var.project_id
  service            = local.services[count.index]
  disable_on_destroy = false
}
