# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests to verify the financing-statement discharges endpoint.

Test-Suite to ensure that the /financing-statement/registrationNum/discharges endpoint is working as expected.
"""
import copy
from http import HTTPStatus

from registry_schemas.example_data.ppr import DISCHARGE_STATEMENT, FINANCING_STATEMENT

from ppr_api.services.authz import STAFF_ROLE, COLIN_ROLE, PPR_ROLE
from tests.unit.services.utils import create_header_account, create_header


# prep sample post discharge statement data
SAMPLE_JSON = copy.deepcopy(DISCHARGE_STATEMENT)


def test_discharge_valid_200(session, client, jwt):
    """Assert that a valid create statement returns a 200 status."""
    # setup - create a financing statement as the base registration, then a discharge
    statement = copy.deepcopy(FINANCING_STATEMENT)
    statement['type'] = 'SA'
    statement['debtors'][0]['businessName'] = 'TEST BUS 2 DEBTOR'
    del statement['createDateTime']
    del statement['baseRegistrationNumber']
    del statement['payment']
    del statement['lifeInfinite']
    del statement['lienAmount']
    del statement['surrenderDate']
    del statement['documentId']

    rv1 = client.post('/api/v1/financing-statements',
                      json=statement,
                      headers=create_header_account(jwt, [PPR_ROLE]),
                      content_type='application/json')
    assert rv1.status_code == HTTPStatus.CREATED
    assert rv1.json['baseRegistrationNumber']
    base_reg_num = rv1.json['baseRegistrationNumber']

    json_data = copy.deepcopy(SAMPLE_JSON)
    json_data['baseDebtor']['businessName'] = 'TEST BUS 2 DEBTOR'
    json_data['baseRegistrationNumber'] = base_reg_num
    del json_data['createDateTime']
    del json_data['dischargeRegistrationNumber']
    del json_data['payment']

    # test
    rv = client.post('/api/v1/financing-statements/' + base_reg_num + '/discharges',
                     json=json_data,
                     headers=create_header_account(jwt, [PPR_ROLE]),
                     content_type='application/json')
    # check
    assert rv.status_code == HTTPStatus.OK


def test_discharge_invalid_missing_basedebtor_400(session, client, jwt):
    """Assert that create statement with a missing base debtor returns a 400 error."""
    # setup
    json_data = copy.deepcopy(SAMPLE_JSON)
    del json_data['createDateTime']
    del json_data['dischargeRegistrationNumber']
    del json_data['payment']
    del json_data['baseDebtor']

    # test
    rv = client.post('/api/v1/financing-statements/023001B/discharges',
                     json=json_data,
                     headers=create_header_account(jwt, [PPR_ROLE]),
                     content_type='application/json')
    # check
    assert rv.status_code == HTTPStatus.BAD_REQUEST


def test_discharge_invalid_regnum_404(session, client, jwt):
    """Assert that a discharge statement on an invalid registration number returns a 404 status."""
    # setup
    json_data = copy.deepcopy(SAMPLE_JSON)
    json_data['baseRegistrationNumber'] = 'X12345X'
    del json_data['createDateTime']
    del json_data['dischargeRegistrationNumber']
    del json_data['payment']

    # test
    rv = client.post('/api/v1/financing-statements/X12345X/discharges',
                     json=json_data,
                     headers=create_header_account(jwt, [PPR_ROLE]),
                     content_type='application/json')

    # check
    assert rv.status_code == HTTPStatus.NOT_FOUND


def test_discharge_invalid_historical_400(session, client, jwt):
    """Assert that a discharge statement on an already discharged registration returns a 400 status."""
    # setup
    json_data = copy.deepcopy(SAMPLE_JSON)
    json_data['baseRegistrationNumber'] = 'TEST0003'
    del json_data['createDateTime']
    del json_data['dischargeRegistrationNumber']
    del json_data['payment']

    # test
    rv = client.post('/api/v1/financing-statements/TEST0003/discharges',
                     json=json_data,
                     headers=create_header_account(jwt, [PPR_ROLE]),
                     content_type='application/json')

    # check
    assert rv.status_code == HTTPStatus.BAD_REQUEST


def test_discharge_invalid_debtor_400(session, client, jwt):
    """Assert that a discharge statement with an invalid base debtor name returns a 400 status."""
    # setup
    json_data = copy.deepcopy(SAMPLE_JSON)
    json_data['baseRegistrationNumber'] = 'TEST0001'
    json_data['baseDebtor']['businessName'] = 'TEST BUS 3 DEBTOR'
    del json_data['createDateTime']
    del json_data['dischargeRegistrationNumber']
    del json_data['payment']

    # test
    rv = client.post('/api/v1/financing-statements/TEST0001/discharges',
                     json=json_data,
                     headers=create_header_account(jwt, [PPR_ROLE]),
                     content_type='application/json')

    # check
    assert rv.status_code == HTTPStatus.BAD_REQUEST


def test_discharge_nonstaff_missing_account_400(session, client, jwt):
    """Assert that a discharge statement request with a non-staff jwt and no account ID returns a 400 status."""
    # setup
    json_data = copy.deepcopy(SAMPLE_JSON)
    json_data['baseDebtor']['businessName'] = 'TEST BUS 2 DEBTOR'
    json_data['baseRegistrationNumber'] = 'TEST0001'
    del json_data['createDateTime']
    del json_data['dischargeRegistrationNumber']
    del json_data['payment']

    # test
    rv = client.post('/api/v1/financing-statements/TEST0001/discharges',
                     json=json_data,
                     headers=create_header(jwt, [COLIN_ROLE]),
                     content_type='application/json')

    # check
    assert rv.status_code == HTTPStatus.BAD_REQUEST


def test_discharge_staff_missing_account_200(session, client, jwt):
    """Assert that a discharge statement request with a staff jwt and no account ID returns a 200 status."""
    # setup
    json_data = copy.deepcopy(SAMPLE_JSON)
    json_data['baseDebtor']['businessName'] = 'TEST BUS 2 DEBTOR'
    json_data['baseRegistrationNumber'] = 'TEST0001'
    del json_data['createDateTime']
    del json_data['dischargeRegistrationNumber']
    del json_data['payment']

    # test
    rv = client.post('/api/v1/financing-statements/TEST0001/discharges',
                     json=json_data,
                     headers=create_header(jwt, [PPR_ROLE, STAFF_ROLE]),
                     content_type='application/json')

    # check
    assert rv.status_code == HTTPStatus.OK


def test_discharge_nonstaff_unauthorized_401(session, client, jwt):
    """Assert that a discharge statement request with a non-ppr role and account ID returns a 404 status."""
    # setup
    json_data = copy.deepcopy(SAMPLE_JSON)
    del json_data['createDateTime']
    del json_data['dischargeRegistrationNumber']
    del json_data['payment']

    # test
    rv = client.post('/api/v1/financing-statements/023001B/discharges',
                     json=json_data,
                     headers=create_header_account(jwt, [COLIN_ROLE]),
                     content_type='application/json')

    # check
    assert rv.status_code == HTTPStatus.UNAUTHORIZED
