# vim:set ts=4 sw=4 et:
'''
ContainerNameTests
------------------
'''

import unittest

from docker_leash.checks.container_name import (ContainerName, path_parameter,
                                                query_parameter)
from docker_leash.exceptions import (InvalidRequestException,
                                     UnauthorizedException)
from docker_leash.payload import Payload

PAYLOAD = {
    "User": "someone",
    "RequestMethod": "POST",
    "RequestUri": "/v1.32/containers/create",
}

PAYLOAD_FOOBAR = {
    "User": "someone",
    "RequestMethod": "POST",
    "RequestUri": "/v1.32/containers/create?name=foo-bar",
}

PAYLOAD_SOMETHING = {
    "User": "someone",
    "RequestMethod": "POST",
    "RequestUri": "/v1.32/containers/create?name=hard-biture",
}

PAYLOAD_USER = {
    "User": "someone",
    "RequestMethod": "POST",
    "RequestUri": "/v1.32/containers/create?name=someone-love-me",
}

PAYLOAD_USERNAME = {
    "User": "someone",
    "RequestMethod": "POST",
    "RequestUri": "/v1.32/containers/create?name=someoneNAME-love-me",
}


class ContainerNameTests(unittest.TestCase):
    """Validation of :cls:`docker_leash.checks.ContainerName`
    """

    def test_empty_payload(self):
        """Empty payload should return :exc:`InvalidRequestException`
        """
        with self.assertRaises(InvalidRequestException):
            ContainerName().run(None, Payload({}))

        with self.assertRaises(InvalidRequestException):
            ContainerName().run(".*", Payload({}))

    def test_name_not_defined(self):
        """Without name return :exc:`UnauthorizedException`
        """
        # This case could be interresting in the future...
        # ContainerName().run("^hard-.*", Payload(PAYLOAD))

        ContainerName().run(".*", Payload(PAYLOAD))
        with self.assertRaises(UnauthorizedException):
            ContainerName().run(".+", Payload(PAYLOAD))

    @staticmethod
    def test_basics():
        """Validate wildcards cases
        """
        ContainerName().run(None, Payload(PAYLOAD_SOMETHING))
        ContainerName().run(None, Payload(PAYLOAD_FOOBAR))
        ContainerName().run(".*", Payload(PAYLOAD_FOOBAR))
        ContainerName().run(".*", Payload(PAYLOAD_SOMETHING))
        ContainerName().run(".+", Payload(PAYLOAD_FOOBAR))
        ContainerName().run(".+", Payload(PAYLOAD_SOMETHING))
        ContainerName().run("", Payload(PAYLOAD_FOOBAR))
        ContainerName().run("", Payload(PAYLOAD_SOMETHING))

    @staticmethod
    def test_valid_names():
        """Valid cases
        """
        ContainerName().run("^foo-.*", Payload(PAYLOAD_FOOBAR))
        ContainerName().run(".*oo.*", Payload(PAYLOAD_FOOBAR))
        ContainerName().run("^hard-.*", Payload(PAYLOAD_SOMETHING))
        ContainerName().run("hard.*", Payload(PAYLOAD_SOMETHING))
        ContainerName().run(".*biture", Payload(PAYLOAD_SOMETHING))
        ContainerName().run("hard-biture", Payload(PAYLOAD_SOMETHING))
        ContainerName().run("hard-bitur", Payload(PAYLOAD_SOMETHING))

    def test_name_can_be_a_list(self):
        """names could be presented as a list

        In such case, entries are compared with a 'or'.
        """
        ContainerName().run(["^foo-.*", "^$USER-.*"], Payload(PAYLOAD_FOOBAR))
        ContainerName().run(["^foo-.*", "^$USER-.*"], Payload(PAYLOAD_USER))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run(["^foo-.*", r"^\$USER-.*"], Payload(PAYLOAD_USER))

    def test_invalid_names(self):
        """Invalid cases
        """
        with self.assertRaises(UnauthorizedException):
            ContainerName().run("^foobar.*", Payload(PAYLOAD_FOOBAR))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run("^bar-foo.*", Payload(PAYLOAD_FOOBAR))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run("bar-foo", Payload(PAYLOAD_FOOBAR))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run("^mega-hard-biture.*", Payload(PAYLOAD_SOMETHING))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run("ard-bitur", Payload(PAYLOAD_SOMETHING))

    def test_username_in_image_name(self):
        """Replace $USER by connected username
        """
        ContainerName().run("^$USER-.*", Payload(PAYLOAD_USER))
        ContainerName().run("^$USERNAME-.*", Payload(PAYLOAD_USERNAME))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run("^$USER-.*", Payload(PAYLOAD_SOMETHING))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run(r"^\$USER-.*", Payload(PAYLOAD_USER))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run(r"^\$USER-.*", Payload(PAYLOAD_SOMETHING))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run("^$USER-.*", Payload(PAYLOAD_USERNAME))

        with self.assertRaises(UnauthorizedException):
            ContainerName().run(r"^\$USER-.*", Payload(PAYLOAD_USERNAME))

    def test_query_parameter(self):
        """Check query_parameter
        """
        self.assertEqual(query_parameter(Payload(PAYLOAD_USER)), "someone-love-me")

    def test_path_parameter(self):
        """Check path_parameter
        """

        payload = {
            "User": "someone",
            "RequestMethod": "DELETE",
            "RequestUri": "/v1.32/containers/someone-love-me",
        }
        self.assertEqual(path_parameter(Payload(payload)), "someone-love-me")

    def test_bad_path_parameter(self):
        """Check path_parameter with invalid uri
        """

        payload = {
            "User": "someone",
            "RequestMethod": "DELETE",
            "RequestUri": "/v1.32/containers/",
        }
        with self.assertRaises(UnauthorizedException):
            self.assertEqual(path_parameter(Payload(payload)), "someone-love-me")
