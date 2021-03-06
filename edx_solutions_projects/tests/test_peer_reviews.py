# pylint: disable=E1103

"""
Run these tests: paver test_system -s lms -t edx_solutions_projects
"""
import uuid
import ddt

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test.utils import override_settings

from edx_solutions_projects.models import Project, Workgroup
from student.models import anonymous_id_for_user
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE
)
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from edx_solutions_api_integration.test_utils import APIClientMixin


class PeerReviewsApiTests(ModuleStoreTestCase, APIClientMixin):

    """ Test suite for Peer Reviews API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super(PeerReviewsApiTests, self).setUp()
        self.test_server_prefix = 'https://testserver'
        self.test_users_uri = '/api/server/users/'
        self.test_workgroups_uri = '/api/server/workgroups/'
        self.test_projects_uri = '/api/server/projects/'
        self.test_peer_reviews_uri = '/api/server/peer_reviews/'

        self.course = CourseFactory.create()
        self.test_data = '<html>{}</html>'.format(str(uuid.uuid4()))

        self.chapter = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            display_name="Overview"
        )

        self.test_course_id = unicode(self.course.id)
        self.test_bogus_course_id = 'foo/bar/baz'
        self.test_course_content_id = unicode(self.chapter.scope_ids.usage_id)
        self.test_bogus_course_content_id = "14x://foo/bar/baz"

        self.test_question = "Does the question data come from the XBlock definition?"
        self.test_answer = "It sure does!  And so does the answer data!"

        self.test_peer_user = User.objects.create(
            email="peer_user@edx.org",
            username="peer",
            is_active=True
        )

        self.test_reviewer_user = User.objects.create(
            email="reviewer_user@edx.org",
            username="reviewer",
            is_active=True
        )
        self.anonymous_user_id = anonymous_id_for_user(self.test_reviewer_user, self.course.id)

        self.test_project = Project.objects.create(
            course_id=self.test_course_id,
            content_id=self.test_course_content_id,
        )

        self.test_workgroup = Workgroup.objects.create(
            name="Test Workgroup",
            project=self.test_project,
        )
        self.test_workgroup.add_user(self.test_peer_user)
        self.test_workgroup.save()

        cache.clear()

    def test_peer_reviews_list_post(self):
        data = {
            'workgroup': self.test_workgroup.id,
            'user': self.test_peer_user.id,
            'reviewer': self.anonymous_user_id,
            'question': self.test_question,
            'answer': self.test_answer,
            'content_id': self.test_course_content_id
        }
        response = self.do_post(self.test_peer_reviews_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = '{}{}{}/'.format(
            self.test_server_prefix,
            self.test_peer_reviews_uri,
            str(response.data['id'])
        )
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['user'], self.test_peer_user.id)
        self.assertEqual(response.data['reviewer'], self.anonymous_user_id)
        self.assertEqual(response.data['question'], self.test_question)
        self.assertEqual(response.data['answer'], self.test_answer)
        self.assertEqual(response.data['workgroup'], self.test_workgroup.id)
        self.assertEqual(response.data['content_id'], self.test_course_content_id)
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_peer_reviews_list_post_invalid_relationships(self):
        data = {
            'user': 123456,
            'reviewer': self.anonymous_user_id,
            'question': self.test_question,
            'answer': self.test_answer,
        }
        response = self.do_post(self.test_peer_reviews_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_peer_reviews_list_get(self):
        data = {
            'workgroup': self.test_workgroup.id,
            'user': self.test_peer_user.id,
            'reviewer': self.anonymous_user_id,
            'question': self.test_question,
            'answer': self.test_answer,
            'content_id': self.test_course_content_id
        }
        response = self.do_post(self.test_peer_reviews_uri, data)
        self.assertEqual(response.status_code, 201)
        data = {
            'workgroup': self.test_workgroup.id,
            'user': self.test_peer_user.id,
            'reviewer': self.anonymous_user_id,
            'question': self.test_question,
            'answer': self.test_answer,
            'content_id': self.test_course_content_id
        }
        response = self.do_post(self.test_peer_reviews_uri, data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(self.test_peer_reviews_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

    def test_peer_reviews_detail_get(self):
        data = {
            'workgroup': self.test_workgroup.id,
            'user': self.test_peer_user.id,
            'reviewer': self.anonymous_user_id,
            'question': self.test_question,
            'answer': self.test_answer,
            'content_id': self.test_course_content_id,
        }
        response = self.do_post(self.test_peer_reviews_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_peer_reviews_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = '{}{}{}/'.format(
            self.test_server_prefix,
            self.test_peer_reviews_uri,
            str(response.data['id'])
        )
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['workgroup'], self.test_workgroup.id)
        self.assertEqual(response.data['user'], self.test_peer_user.id)
        self.assertEqual(response.data['reviewer'], self.anonymous_user_id)
        self.assertEqual(response.data['question'], self.test_question)
        self.assertEqual(response.data['answer'], self.test_answer)
        self.assertEqual(response.data['content_id'], self.test_course_content_id)
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_peer_reviews_detail_get_undefined(self):
        test_uri = '{}/123456789/'.format(self.test_peer_reviews_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_peer_reviews_detail_delete(self):
        data = {
            'workgroup': self.test_workgroup.id,
            'user': self.test_peer_user.id,
            'reviewer': self.anonymous_user_id,
            'question': self.test_question,
            'answer': self.test_answer,
        }
        response = self.do_post(self.test_peer_reviews_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_peer_reviews_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
