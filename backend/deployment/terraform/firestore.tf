# First real provisioning of backend's production Firestore database --
# previously only ever exercised via the local emulator. A GCP project can
# have only one default Firestore database, and its type can't be changed
# after creation -- apply this deliberately, not as a side effect of
# unrelated changes.
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.services]
}
