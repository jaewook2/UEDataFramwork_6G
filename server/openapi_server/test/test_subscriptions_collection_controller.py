import unittest

from flask import json

from openapi_server.models.nue_event_exposure import NueEventExposure  # noqa: E501
from openapi_server.models.problem_details import ProblemDetails  # noqa: E501
from openapi_server.test import BaseTestCase


class TestSubscriptionsCollectionController(BaseTestCase):
    """SubscriptionsCollectionController integration test stubs"""

    def test_create_individual_subcription(self):
        """Test case for create_individual_subcription

        Create an individual subscription for event notifications from the UE
        """
        nue_event_exposure = {"notifId":"notifId","notifUri":"notifUri","eventSubs":[{"event":"Location"},{"event":"Location"}]}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/nue-event-exposure/v1/subscriptions',
            method='POST',
            headers=headers,
            data=json.dumps(nue_event_exposure),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
