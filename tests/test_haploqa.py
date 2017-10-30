import unittest
import haploqa.haploqaapp as hqa
import haploqa.mongods as mdb
from bson import ObjectId

class TestHaploQA(unittest.TestCase):
    """
    Class for testing HaploQA
    """

    @classmethod
    def setUpClass(cls):
        tester_email = 'tester@testers.dk'
        cls._tester_email = tester_email
        db = mdb.get_db()
        # find a user to duplicate
        user = db.users.find_one(({'administrator': False}))
        test_user = user
        uid = ObjectId()
        test_user['_id'] = uid
        test_user['email_address_lowercase'] = tester_email
        test_user['email_address'] = tester_email
        db.users.insert_one(test_user)
        # make the user id available to the tests
        cls._uid = uid
        print("Setup: Created test user {}".format(uid))
        # find a private sample not owned by the test user
        cls._private_sample = db.samples.find_one({'is_public': False, 'owner': {'$exists': True, '$nin': [tester_email]}})
        print("Setup: private sample id: {}".format(cls._private_sample['_id']))
        sample = db.samples.find_one({'sample_id': "32C"})
        sample2 = sample
        sample_id = ObjectId()
        print("Setup: test sample id is {}".format(sample_id))
        sample2['_id'] = sample_id
        #make the id available to the tests
        cls._sample_id = sample_id
        sample2['sample_id'] = 'unit_tester'
        sample2['tags'] = 'unit_testing_tag'
        sample2['is_public'] = True
        sample2['owner'] = tester_email
        db.samples.insert_one(sample2)
        print("Setup: creating test client")
        client = hqa.app.test_client()
        # make the flask test client available for the tests
        cls._client = client
        # make the db connection available for the tests
        cls._db = db
        # edit button html for samples page
        button = '<button id="edit-{}-button" type="button" class="btn btn-primary">'
        cls._edit_sample_button = button.format('sample')
        cls._edit_samples_button = button.format('samples')

    @classmethod
    def tearDownClass(cls):
        cls._db.samples.delete_one({"sample_id": "unit_tester"})
        print("Teardown: removed test sample")
        cls._db.users.delete_one({"email_address_lowercase": cls._tester_email})
        print("Teardown: removed test user")

    def setUp(self):
        # clear the session
        self._set_session()

    def tearDown(self):
        #clear the session and reset test user priviliges
        self._set_session()
        self._switch_admin()

    ### Utility Functions ###
    def _set_session(self, admin=False, email=None):
        """
        set the session privileges or clear the session (setting user email)
        :param admin: True / False
        :param email: the users email address, or None to have no login
        :return:
        """

        with self._client.session_transaction() as sess:
            sess['user_email_address'] = email
            sess['administrator'] = admin
            sess['remote_addr'] = '127.0.0.1'

    def _switch_admin(self, admin=False):
        """
        switch the test user's privileges to/from admin
        :param admin: True / False
        :return:
        """

        self._db.users.update_one(
            {"email_address_lowercase": self._tester_email},
            {'$set':
                {
                    "administrator": admin
                },
            })

    ### Unit Tests ###

    def test_home_page(self):
        """ test the home page as unauthenticated user"""

        req = self._client.get("tag/GigaMUGA.html")
        self.assertEqual(req.status, '200 OK')

    def test_private_sample(self):
        """hit private sample and verify it can't be viewed by an unauthenicated user"""

        req = self._client.get("sample/{}.html".format(self._private_sample['_id']))
        self.assertIn('Login Required', str(req.data))

    def test_public_sample(self):
        """test that you can view (but not edit) a public sample as a non-authenticated user"""

        req = self._client.get("sample/{}.html".format(self._sample_id))
        # make sure the not found / login page is not displayed
        self.assertNotIn('Login Required', str(req.data))
        # make sure you cannot edit the sample
        self.assertNotIn(self._edit_sample_button, str(req.data))

    def test_private_sample_authenticated(self):
        """test you can view but not edit a private sample"""

        # set default session
        self._set_session(False, self._tester_email)
        req = self._client.get("sample/{}.html".format(self._private_sample['_id']))
        # make sure you have an active session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure that you get the sample page but not the edit button
        self.assertNotIn(self._edit_sample_button, str(req.data))

    def test_private_sample(self):
        """verify the regular user can see the sample tag on, but not edit the tags page"""

        # hit the tags page - the sample should not be there
        req = self._client.get("tag/unit_testing_tag.html".format(self._private_sample['_id']))
        # make sure you have an actve session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure you don't see the sample tag on the page
        # make sure that you get the sample page but not the edit button
        self.assertIn('unit_testing_tag', str(req.data))

    def test_edit_sample(self):
        """test that the test user can edit a sample owned by them"""

        # set default session
        self._set_session(False, self._tester_email)
        req = self._client.get("sample/{}.html".format(self._sample_id))
        # make sure you have an active session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure that you get the sample page but not the edit button
        self.assertIn(self._edit_sample_button, str(req.data))

    def test_edit_sample_not_owned(self):
        """test that a regular user cannot edit a sample owned by another user"""

        # set default session
        self._set_session(False, self._tester_email)
        req = self._client.get("sample/{}.html".format(self._private_sample['_id']))
        # make sure you have an active session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure that you get the sample page but not the edit button
        self.assertNotIn(self._edit_sample_button, str(req.data))

    def test_user_samples(self):
        """testing permissions on user samples page"""

        req = self._client.get("user-samples/{}".format(self._uid))
        self.assertIn('Login Required', str(req.data))
        # set session for test user
        self._set_session(False, self._tester_email)
        req = self._client.get("user-samples/{}".format(self._uid))
        self.assertIn('Login Required', str(req.data))

    def test_user_samples_admin(self):
        """verify you can see the user samples page as admin, the test sample is there, and you can edit the page"""

        # promote user to admin and set session
        self._switch_admin(True)
        self._set_session(True, self._tester_email)
        req = self._client.get("user-samples/{}".format(self._uid))
        # make sure you can see the page
        self.assertNotIn('Login Required', str(req.data))
        # verify you can see the sample
        self.assertIn('unit_tester', str(req.data))
        # verify the edit button is available
        self.assertIn(self._edit_samples_button, str(req.data))

    def test_user_admin_unauthorized(self):
        """verify that non-authenticated users nor non-admin cannot see the user admin page"""

        # make sure you're not logged in
        self._set_session()
        self._set_session(False, self._tester_email)
        req = self._client.get("show-users.html")
        self.assertIn('not authorized', str(req.data))
        # set session for test user
        self._switch_admin()
        req = self._client.get("show-users.html")
        self.assertIn('not authorized', str(req.data))

    def test_user_admin(self):
        """verify that as admin you can see the user admin page"""

        # set default session
        self._switch_admin(True)
        self._set_session(True, self._tester_email)
        req = self._client.get("show-users.html")
        self.assertNotIn('not authorized', str(req.data))

    def test_admin_edit_sample(self):
        """test that an admin can edit a sample they don't own"""

        # promote the test user to admin
        self._switch_admin(True)
        # set users session to admin
        self._set_session(True, self._tester_email)

        req = self._client.get("sample/{}.html".format(self._private_sample['_id']))
        # make sure you have an active session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure that you get the sample page but not the edit button
        self.assertIn(self._edit_sample_button, str(req.data))

    def test_owner_tags_unauthenticated(self):
        """verify you cannot see the owner tags page when not logged in"""

        req = self._client.get("owner-tags/unit_testing_tag.html")
        self.assertIn('Login Required', str(req.data))

    def test_owner_tags(self):
        """verify you can see the owner tags page and the test sample when logged in"""

        # set the default session
        self._set_session(False, self._tester_email)
        req = self._client.get("owner-tags/unit_testing_tag.html")
        # make sure you can see the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure you can see the test sample
        self.assertIn('unit_tester', str(req.data))

    def test_user_tags_unauthenticated(self):
        """verify you cannot see the owner tags page when not logged in"""

        req = self._client.get("user-tags.html")
        self.assertIn('Login Required', str(req.data))

    def test_user_tags(self):
        """verify you can see the test tag when logged in"""

        self._set_session(False, self._tester_email)
        req = self._client.get("user-tags.html")
        # verify you can see the page
        self.assertNotIn('Login Required', str(req.data))
        # verify you can see your tag
        self.assertIn('unit_testing_tag', str(req.data))

    def test_tags_page(self):
        """elevate user to admin and verify you can edit the tags page"""
        # set the default session
        self._set_session(True, self._tester_email)
        # elevate user to admin
        self._switch_admin(True)
        req = self._client.get("tag/unit_testing_tag.html")
        self.assertIn(self._edit_samples_button, str(req.data))

    def _test_get_sample(self):
        """see if the test sample exists"""
        db = mdb.get_db()
        sample = db.samples.find_one({'sample_id': "unit_tester"})
        if sample:
            print("sample id: {}, visibility: {}, owner: {}".format(sample['_id'], sample['is_public'], sample['owner']))
        else:
            print("no test sample found!")