"""Streamlit's actual script/state execution, in addition to real-browser QA."""
import pytest
from streamlit.testing.v1 import AppTest

from src.common import ROOT


@pytest.fixture
def app():
    if not (ROOT / "reports/readiness.json").exists():
        pytest.skip("Run pipeline and generate_reports first")
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()


def test_all_six_pages_render(app):
    assert not app.exception
    pages = list(app.sidebar.radio[0].options)
    assert len(pages) == 6
    for name in pages:
        app.sidebar.radio[0].set_value(name).run()
        assert not app.exception, (name, app.exception)
        assert not app.error, (name, app.error)


def test_optimization_budget_and_human_review(app):
    app.sidebar.radio[0].set_value("Budget Optimization").run()
    app.number_input[0].set_value(1500.).run()
    app.button[0].click().run()
    assert not app.exception
    assert any("OPTIMAL" in str(m.value) for m in app.metric)
    [b for b in app.button if b.label == "Accept simulated plan"][0].click().run()
    assert any("No purchase was submitted" in x.value for x in app.success)
    [b for b in app.button if b.label == "Reject simulated plan"][0].click().run()
    assert any("Rejected" in x.value for x in app.success)
    app.number_input[0].set_value(0.).run()
    assert len(app.success) == 0
    app.number_input[0].set_value(1500.).run()
    assert len(app.success) == 0  # Returning to an old budget cannot restore an approval.
    app.number_input[0].set_value(0.).run()
    app.button[0].click().run()
    assert any(m.value == "£0" for m in app.metric)


def test_edit_inventory_form_changes_recommendation(app):
    app.sidebar.radio[0].set_value("Inventory Recommendations").run()
    initial = app.session_state["inventory_inputs"].copy()
    app.session_state["inventory_grid"] = {"edited_rows": {0: {"current_inventory": 99999}}, "added_rows": [], "deleted_rows": []}
    [b for b in app.button if b.label == "Apply assumptions"][0].click().run()
    assert not app.exception
    updated = app.session_state["inventory_inputs"]
    assert updated.iloc[0].current_inventory == 99999
    assert initial.iloc[0].current_inventory < 99999


def test_missing_artifacts_show_actionable_message(monkeypatch):
    # Error-path rendering uses the actual app; valid-path tests above use real artifacts.
    from src import dashboard_data
    import streamlit as st
    st.cache_data.clear()
    monkeypatch.setattr(dashboard_data, "load_dashboard", lambda: (_ for _ in ()).throw(FileNotFoundError("missing prepared data")))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.error and "not ready" in app.error[0].value
    st.cache_data.clear()
