import unittest

from flask import json

from openapi_server.models.nue_event_exposure import NueEventExposure  # noqa: E501
from openapi_server.models.problem_details import ProblemDetails  # noqa: E501
from openapi_server.models.redirect_response import RedirectResponse  # noqa: E501
from openapi_server.test import BaseTestCase


class TestIndividualSubscriptionDocumentController(BaseTestCase):
    """IndividualSubscriptionDocumentController integration test stubs"""

    def test_delete_individual_subcription(self):
        """Test case for delete_individual_subcription

        Delete an individual subscription for event notifications from the UE
        """
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/nue-event-exposure/v1/subscriptions/{sub_id}'.format(sub_id='sub_id_example'),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_individual_subcription(self):
        """Test case for get_individual_subcription

        Read an individual subscription for event notifications from the UE
        """
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/nue-event-exposure/v1/subscriptions/{sub_id}'.format(sub_id='sub_id_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_replace_individual_subcription(self):
        """Test case for replace_individual_subcription

        Replace an individual subscription for event notifications from the UE
        """
        nue_event_exposure = {"notifId":"notifId","notifUri":"notifUri","eventSubs":[{"event":"Location"},{"event":"Location"}]}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/nue-event-exposure/v1/subscriptions/{sub_id}'.format(sub_id='sub_id_example'),
            method='PUT',
            headers=headers,
            data=json.dumps(nue_event_exposure),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
