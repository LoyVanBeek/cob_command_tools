import inspect

from six.moves import input

from scenario_test_tools.scriptable_base import ScriptableBase


class ManualBase(ScriptableBase):
    """
    ManualBase is a variant of ScriptableBase that functions as an interface to a human to confirm
    when a non-mocked implementation has done what the script expects.
    """
    def __init__(self, name, _action_type, goal_formatter=format, reply_formatter=format):
        ScriptableBase.__init__(self, name,
                                goal_formatter=goal_formatter,
                                reply_formatter=reply_formatter)

    def __repr__(self):
        return "ManualBase('{}')".format(self._name)

    def reply(self, result, timeout=None, reply_delay=None, marker=None):
        print('\n########  {}.reply{}  ###########'.format(self._name, '({})'.format(marker) if marker else ''))
        input("Press [Enter] when the call to {} has completed by the robot: ".format(self.name))

    def reply_conditionally(self, condition, true_result, false_result, timeout=None, reply_delay=None, marker=None):
        print('\n########  {}.reply_conditionally{}  ###########'
            .format(self._name, '({})'.format(marker) if marker else ''))

        assert self._waiting_for is None, "reply{} cannot follow an 'await_goal', use reply_directly".format('({})'.format(marker) if marker else '')

        match = 'y' == input("Press [y] or [n] when the call to {} was matches the condition `{}`: "
                             .format(self, inspect.getsource(condition).strip()))

        return match

    def await_goal(self, timeout=None, marker=None):
        """
        Await a goal to be sent to this Scriptable... and return that goal for close inspection.
        Based on that, send a reply via `direct_reply`
        An AssertionError is raised when a goal is not received within the given timeout.

        :param timeout: how long to wait for the goal? Defaults to None to wait indefinitely
        :param marker: A str that is printed in the output for easy reference between different replies
        :return: the received goal
        """
        print('\n########  {}.await_goal{}  ###########'
            .format(self._name, '({})'.format(marker) if marker else ''))
        self.default_reply = None

        input("Press [Enter] when {} has been called/started: ".format(self.name))

        self._waiting_for = 'direct_reply'

        return self._current_goal

    def assert_called_with(self, expected, condition=lambda actual, expected: actual == expected, timeout=None, marker=None):
        print('\n########  {}.assert_called_with{}  ###########'
            .format(self._name, '({})'.format(marker) if marker else ''))
        self.default_reply = None

        assert input("Press [y] or [n] when the call to {} matches the condition `{}` for expected goal {}: "
                     .format(self, inspect.getsource(condition).strip(), self.goal_formatter(expected))) \
               in ['y', '']

        self._waiting_for = 'direct_reply'

    def direct_reply(self, result, reply_delay=None, marker=None):
        """
        Reply to the current goal with the given result, after `reply_delay` amount of seconds.

        :param result: a ...Result of the type associated with the type of this server
        :param reply_delay: how long to 'reply_delay/calculate' on this goal before sending the reply
        :param marker: A str that is printed in the output for easy reference between different replies
        """
        assert self._waiting_for == 'direct_reply', "reply cannot follow an 'await_goal', use reply_directly"

        input("Press [Enter] when {} has finished: ".format(self.name))

        self._waiting_for = None

    def match_in_received_goals(self, match_against, key=lambda x: x):
        """
        Find out if this server has any goal in it's history that is also in `match_against`

        :param match_against: We're looking for any of the items in `match_against`
        :param key: optionally transform the received goals with this callable into the same type as `match_against`'s elements
        :return: The matching elements
        """
        assert input("Press [y] or [n] when {} was called with a goal matching condition `{}`: "
                     .format(self, inspect.getsource(match_against).strip())) \
               in ['y', '']
        return {True}
