def test_reports_create_missing_output_directories(tmp_path, monkeypatch):
    from src import reporting
    monkeypatch.setattr(reporting, "ROOT", tmp_path)
    reporting.save("project-management/evidence.md", "Measured evidence")
    assert (tmp_path / "project-management/evidence.md").read_text() == "Measured evidence\n"
