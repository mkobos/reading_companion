from app.telemetry import _cloud_trace_enabled, setup_tracing


def test_cloud_trace_disabled_by_default():
    assert _cloud_trace_enabled({}) is False


def test_cloud_trace_disabled_when_flag_false():
    assert _cloud_trace_enabled({"ENABLE_CLOUD_TRACE": "false"}) is False


def test_cloud_trace_disabled_when_flag_true_but_no_project():
    assert _cloud_trace_enabled({"ENABLE_CLOUD_TRACE": "true"}) is False


def test_cloud_trace_enabled_when_flag_true_and_project_set():
    env = {"ENABLE_CLOUD_TRACE": "true", "GOOGLE_CLOUD_PROJECT": "some-project"}
    assert _cloud_trace_enabled(env) is True


def test_setup_tracing_is_noop_with_no_env(monkeypatch):
    monkeypatch.delenv("ENABLE_CLOUD_TRACE", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("OTEL_CONSOLE_EXPORT", raising=False)

    _provider, cloud_enabled = setup_tracing()

    assert cloud_enabled is False


def test_setup_tracing_fails_open_when_exporter_construction_raises(monkeypatch):
    monkeypatch.setenv("ENABLE_CLOUD_TRACE", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "some-project")

    def _boom(*args, **kwargs):
        raise RuntimeError("no credentials available")

    monkeypatch.setattr("app.telemetry.CloudTraceSpanExporter", _boom)

    _provider, cloud_enabled = setup_tracing()

    assert cloud_enabled is False


class _FakeSpanExporter:
    def export(self, spans):
        pass

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=30000):
        return True


def test_setup_tracing_activates_cloud_export_when_configured(monkeypatch):
    monkeypatch.setenv("ENABLE_CLOUD_TRACE", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "some-project")
    monkeypatch.setattr(
        "app.telemetry.CloudTraceSpanExporter", lambda *a, **k: _FakeSpanExporter()
    )

    provider, cloud_enabled = setup_tracing()

    assert cloud_enabled is True
    provider.shutdown()
