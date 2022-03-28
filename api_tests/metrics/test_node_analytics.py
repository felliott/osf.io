import pytest

# from osf.metrics import PageView
from osf_tests.factories import NodeFactory


@pytest.mark.django_db
class TestNodeAnalytics:

    @pytest.fixture
    def node(self):
        return NodeFactory()

    def test_get_analytics(self, app):
        node = NodeFactory()

        # TODO-quest: PageView.record(...) sev'ral times

        node_analytics_url = f'/_/metrics/node_analytics/{node._id}/week/'
        response = app.get(node_analytics_url)
        assert response.status_code == 200
