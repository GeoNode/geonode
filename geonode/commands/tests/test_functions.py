#########################################################################
#
# Copyright (C) 2021 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.test import TestCase
from django.contrib.auth import get_user_model
from celery.result import AsyncResult
from geonode.commands.tasks import enqueue_jobs
import time


class TestEnqueueJobs(TestCase):

    def setUp(self):

        # Our test_command needs 1 args, 'type' and 2 kwargs: cpair, ppair
        self.payload = {
        "cmd": "test_command",
        "args": ["delta"],
        "kwargs": {
                "cpair": [10, 40],
                "ppair": ["a", "b"]
            }
        }

        self.wrong_args = [3, 4]
        self.super_user, _ = get_user_model().objects.get_or_create(
            username="superuser", is_staff=True, is_superuser=True
        )

    def test_with_wrong_args_function_is_non_blocking(self):
        """
        Test to prove although we are passing args which raises error but
        because our implementation is async, it is not blocked.

        TODO!! After we add commands.models.job's status update logic we
        should test, that although the processes are not blocked but a task
        with wrong args EITHER "failed" OR entry is deleted on failure, as is
        desirable.
        """

        got_error = False

        try:
            res = enqueue_jobs(*self.wrong_args)
        except Exception:
            got_error = True

        self.assertTrue(got_error)

        res = enqueue_jobs.delay(*self.wrong_args)
        self.assertTrue(isinstance(res, AsyncResult))

    def test_function_is_non_blocking_for_any_process_length(self):
        """
        Our test_command's process has 5 seconds' sleep time. Ensure
        async implementation does not block for this time.
        """
        got_error = False
        t1 = time.time()
        try:
            res = enqueue_jobs(
                self.super_user,
                self.payload["cmd"],
                *self.payload["args"],
                **self.payload["kwargs"]
            )
        except Exception:
            got_error = True

        t2 = time.time()

        # No error but blocked for at least 5 secs.
        self.assertFalse(got_error)
        self.assertGreater(t2 - t1, 5)

        t1 = time.time()
        res = enqueue_jobs.delay(
            self.super_user.id,
            self.payload["cmd"],
            *self.payload["args"],
            **self.payload["kwargs"]
        )
        t2 = time.time()

        # Neither error not blocked for 5 secs.
        self.assertTrue(isinstance(res, AsyncResult))
        self.assertLess(t2 - t1, 5)
