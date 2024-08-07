import pytest

from api.base.settings.defaults import API_BASE
from osf_tests.factories import (
    InstitutionFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestInstitutionUsersList:

    def test_return_all_users(self, app):
        institution = InstitutionFactory()

        user_one = UserFactory()
        user_one.add_or_update_affiliated_institution(institution)
        user_one.save()

        user_two = UserFactory()
        user_two.add_or_update_affiliated_institution(institution)
        user_two.save()

        url = f'/{API_BASE}institutions/{institution._id}/users/'
        res = app.get(url)

        assert res.status_code == 200

        ids = [each['id'] for each in res.json['data']]
        assert len(res.json['data']) == 2
        assert user_one._id in ids
        assert user_two._id in ids
