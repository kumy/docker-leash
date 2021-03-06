# vim:set ts=4 sw=4 et:
'''
Config
======
'''

import re

from .action_mapper import Action
from .checks_list import Checks
from .exceptions import ConfigurationException


class Config(object):
    """The :class:`Config` class is responsible for storing application groups
    and policies read from the datastore.

    It has some handy functions to extract values from the configuration.
    It can respond to questions such as:

    * "Which are the groups for a user?"
    * "Which policies user belong to?"
    * "Which tests are enabled for a user?"

    :var groups: The groups.
    :vartype groups: dict or None
    :var policies: The policies.
    :vartype policies: dict or None

    :param groups: The groups.
    :type groups: dict or None
    :param policies: The policies.
    :type policies: dict or None
    """

    #: The loaded policies
    policies = None

    #: The loaded groups
    groups = None

    def __init__(self, groups=None, policies=None):
        self.update(groups, policies)

    def update(self, groups=None, policies=None):
        """Update the stored configuration with the provided values.

        :param groups: The groups.
        :type groups: dict or None
        :param policies: The policies.
        :type policies: dict or None
        """
        if groups:
            if self.groups:
                self.groups.update(groups)
            else:
                self.groups = groups

        if policies:
            self.policies = policies

    def get_rules(self, payload):
        """Return the rules for a payload.

        :param str payload: The current payload.
        :return: The rules concerned by the payload.
        :rtype: list
        """
        username = payload.user
        action = Action(method=payload.method, query=payload.uri)
        hostname = payload.get_host()

        for rule in self.policies:
            if not self._match_host(hostname, rule["hosts"]):
                continue

            if "policies" not in rule:
                return self._default_rule(rule)

            policies = self._get_policy_by_member(username, rule["policies"])
            if policies is None:
                return self._default_rule(rule)

            rules = self._match_rules(action, policies)
            if not rules:
                return self._default_rule(rule)

            return rules

    @staticmethod
    def _default_rule(rule):
        """Construct a default rule

        :param dict rule: The current parsed rule
        :return: A :class:`~docker_leash.checks_list.Checks_list.Checks` containing only the default rule
        :rtype: :class:`~docker_leash.checks_list.Checks_list.Checks`
        """
        checks = Checks()
        checks.add(rule["default"])
        return checks

    @staticmethod
    def _match_host(hostname, host_rules):
        """Validate if a hostname match hosts regex list

        :param str hostname: The hostname
        :param list host_rules: List of hosts regex
        :return: True if hostname match host rules
        :rtype: bool
        :raises ConfigurationException: if the host rules are invalid.
        """
        match = False
        for hosts_reg in host_rules:
            mode = hosts_reg[0]
            regex = hosts_reg[1:]

            if mode == '+':
                if re.match(regex, hostname):
                    match = True
                    continue
            elif mode == '-':
                if re.match(regex, hostname):
                    match = False
                    continue
            else:
                raise ConfigurationException(
                    "'hosts' regex (%s) is missing '+' or '-'" % hosts_reg
                )
        return match

    def _get_policy_by_member(self, username, policies):
        """Extract the policies for a user name.

        Return the concerned policies:
          * If the user match in a group
          * If the user is None, and "members" contains "Anonymous"
          * Else return None

        :param str username: The username
        :param dict policies: The policies to filter
        :return: The policies for username
        :rtype: None or dict
        """
        for policy in policies:

            for group in policy["members"]:
                if group in self.groups:
                    if username in self.groups[group] \
                            or "*" in self.groups[group] \
                            or (username is None and "Anonymous" in self.groups[group]):
                        return policy["rules"]
        return None

    @staticmethod
    def _match_rules(action, actions):
        """Extract the checks for an action.

        First match for exact comparison, then for the "any" keyword,
        and finally for "parents" action name.

        :param docker_leash.action_mapper.Action action: The current action
        :param dict actions: The actions from the policies
        :return: The filtered actions list
        :rtype: `~docker_leash.checks_list.Checks`
        """
        assert isinstance(action, Action), 'expected Action, got {!r}'.format(action)
        checks = Checks()
        action_name = action.name
        parent_action = action.namespace_name

        # Look for "normal" Actions
        if action_name in actions:
            for check, args in actions[action_name].iteritems():
                checks.add({check: args})

        # Look for "parents" Actions
        elif parent_action in actions:
            for check, args in actions[parent_action].iteritems():
                checks.add({check: args})

        # Look for "any" Actions
        elif "any" in actions:
            for check, args in actions["any"].iteritems():
                checks.add({check: args})

        return checks
