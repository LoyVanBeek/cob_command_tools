#!/usr/bin/env python
#
# Copyright 2020 Mojin Robotics GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO:
# What should you be able to do with this:
# - Check that config is getting changed at all
# - Verify a particular key was set to a particular value
# - The above for a collection of keys, maybe in 1 call
# - Just accept all changes but verify the current setting is #
import pprint
from collections import OrderedDict

import rospy
from dynamic_reconfigure.server import Server

from scenario_test_tools.scriptable_base import ScriptableBase
from scenario_test_tools.util import countdown_sleep


class ScriptableDynamicReconfigureServer(ScriptableBase):
    ACCEPT = 'ACCEPT'

    def __init__(self, namespace, cfg_type,
                 cfg_formatter=lambda cfg: pprint.pformat(dict(cfg)),
                 default_response=ACCEPT,
                 default_response_delay=0):
        super(ScriptableDynamicReconfigureServer, self).__init__(
            namespace,
            goal_formatter=cfg_formatter,
            reply_formatter=cfg_formatter,
            default_reply=default_response,
            default_reply_delay=default_response_delay)

        self._current_cfg = None
        self._server = Server(type=cfg_type, callback=self._process_cfg, namespace=namespace)

    @property
    def current_cfg(self):
        return self._current_cfg

    def _process_cfg(self, cfg, level):
        """
        Called when the underlying dynamic-reconfigure Server gets a request to update the config
        If the default_reply is set to `ACCEPT`, the new config is accepted and copied without issue and changes,
        after the default_reply_delay.

        If the default_result is None, it will wait for a custom configuration to be set via reply*.

        In the reply-case, this _process_cfg then notifies self.reply* (which should be called by a test script outside this class),
        after which self.reply* determines the result to the goal.
        Then it notifies _process_cfg that the result has been determined so that _process_cfg can send it
        """

        self._current_goal = cfg

        try:
            request_str = self.goal_formatter(self._current_goal)
        except Exception as e:
            rospy.logerr("request_formatter of {} raised an exception: {}".format(self._name, e))
            request_str = self._current_goal
        print('{}.execute: Request: {}'.format(self._name, request_str))

        if self.default_reply == self.ACCEPT:
            new_cfg = cfg
            countdown_sleep(self._default_reply_delay, text="{} accept config: Wait for {}s. "
                            .format(self._name, self._default_reply_delay) + "Remaining {}s...")
        elif self.default_reply is None:
            self._request.set()
            # Now, wait for  to be called, which sets the _reply event AND the _next_reply
            self._reply.wait()
            self._reply.clear()

            if type(self._next_reply) == type(cfg):
                new_cfg = self._next_reply
            elif self._next_reply == self.ACCEPT:
                new_cfg = cfg
            elif isinstance(self._next_reply, dict):
                new_cfg = cfg
                new_cfg.update(self._next_reply)

            self._next_reply = None
            self._current_goal = None
            self._sent.set()
        else:
            rospy.logerr("Invalid self.default_reply: {}, accepting".format(self.default_reply))
            exit(-1)
            return

        self._current_cfg = new_cfg
        self._call_pre_reply_callbacks(cfg, new_cfg)
        return new_cfg
