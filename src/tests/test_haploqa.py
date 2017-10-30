import unittest
import haploqa.haploqaapp as hqa
import haploqa.mongods as mdb

class TestHaploQA(unittest.TestCase):
    """
    Class for testing HaploQA
    """

    @classmethod
    def setUpClass(cls):
        pass
        tester_email = 'tester@testers.dk'
        cls._tester_email = tester_email
        db = mdb.get_db()
        # find a user to duplicat
        user = db.users.find_one(({'administrator': False}))
        test_user = user
        test_user['_id'] = 'testuserID'
        test_user['email_address_lowercase'] = tester_email
        #db.users.insert_one(test_user)
        # find a sample to duplicate
        cls._private_sample = db.samples.find_one({'is_public': False, 'owner': {'$exists': True, '$nin': [tester_email]}})
        print("private sample id: {}".format(cls._private_sample['_id']))
        sample = db.samples.find_one({'sample_id': "32C"})
        sample2 = sample
        # TODO: this key is not working on the sample page
        # using tags page for now
        sample_id = '93114124bd0411e78a091865'
        print("test sample id is {}".format(sample_id))
        sample2['_id'] = sample_id
        #make the id available to the tests'''
        cls._sample_id = '583d77863ac36a08a0040c7c'
        sample2['sample_id'] = 'unit_tester'
        sample2['tags'] = 'unit_testing_tag'
        sample2['is_public'] = False
        sample2['owner'] = tester_email
        db.samples.insert_one(sample2)
        print("Setup: created test sample")
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

    def test_home_page(self):
        """ test the home page"""

        req = self._client.get("tag/GigaMUGA.html")
        self.assertEqual(req.status, '200 OK')

    # utility functions
    def _set_session(self, admin=False, email=None):
        """
        set the session privileges
        :param admin: True / False
        :return:
        """

        with self._client.session_transaction() as sess:
            # dont need a real email as this is just faking the session
            if email is None:
                email = self._tester_email
            sess['user_email_address'] = email
            sess['administrator'] = admin
            sess['remote_addr'] = '127.0.0.1'

    def _switch_admin(self, admin=False):
        """
        switch the test user's privileges to/from admin
        :param admin:
        :return:
        """

        self._db.users.update_one(
            {"email_address_lowercase": self._tester_email},
            {'$set':
                {
                    "administrator": admin
                },
            })

    def test_public_sample(self):
        """test unauthenticated user can view public sample but not edit it"""
        # TODO: need to find a way to get a public sample, query not working
        req = self._client.get("sample/5783c0073ac36a16331c00fe/.html")
        # make sure you have an active session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure that you get the sample page but not the edit button
        self.assertNotIn(self._edit_sample_button, str(req.data))


    #TODO: not goign to work until I can get the sample endpoint working correctly
    def test_private_sample(self):
        """hit private sample and verify it can't be viewed by an unauthenicated user"""

        req = self._client.get("sample/{}.html".format(self._private_sample['_id']))
        self.assertIn('Login Required', str(req.data))

    def test_private_sample_for_regular_user(self):
        """test you can view but not edit a private sample"""

        # reset test user to regular and set default session
        self._switch_admin()
        self._set_session()
        req = self._client.get("sample/{}.html".format(self._private_sample['_id']))
        # make sure you have an active session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure that you get the sample page but not the edit button
        self.assertNotIn(self._edit_sample_button, str(req.data))

    # TODO: need to get a test sample working or designate one as test, owned by test user, etc
    # TODO verify you can edit your own sample


    # TODO: not going to work until I can get the sample endpoint working correctly.
    def test_private_sample(self):
        """verify the regular user can see the sample tag on, but not edit the tags page"""

        # set session default - regular user
        self._set_session()

        # update the test sample to private
        self._switch_admin(False)

        # hit the tags page - the sample should not be there
        req = self._client.get("tag/unit_testing_tag.html".format(self._private_sample['_id']))
        # make sure you have an actve session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure you don't see the sample tag on the page
        # make sure that you get the sample page but not the edit button
        self.assertIn('unit_testing_tag', str(req.data))

        # switch user back to regular
        self._switch_admin()

    # TODO: change the sample's ownership and verify you can't edit it as a regular user
    def test_edit_sample(self):
        """test that a regular user cannot edit a sample owned by another user"""

        # set default session and privs
        self._switch_admin()
        self._set_session()
        req = self._client.get("sample/{}.html".format(self._private_sample['_id']))
        # make sure you have an active session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure that you get the sample page but not the edit button
        self.assertNotIn(self._edit_sample_button, str(req.data))


    def test_admin_can_edit_sample_not_owned_by_them(self):
        """test that an admin can edit a sample they don't own"""

        self.test_get_sample()
        # set users status to admin
        # promote the test user to admin
        self._switch_admin(True)
        self._set_session(True)

        req = self._client.get("sample/{}.html".format(self._private_sample['_id']))
        # make sure you have an active session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure that you get the sample page but not the edit button
        self.assertIn(self._edit_sample_button, str(req.data))


    # TODO: need to block access to this page
    def _test_user_tags_unauthenticated(self):
        """verify as a non-authenticated user you cannot see the user tags page"""

        # use a non-existant user email to fake a non-authenticated session
        #self._set_session(False, 'no@user.com')
        req = self._client.get("tag/user-tags.html")
        self.assertIn('Login Required', str(req.data))

    def test_user_tags_authenticated(self):
        """verify you can see the test sample authenticated as a regular user"""

        # set session defaults
        #self._set_session()
        req = self._client.get("tag/user-tags.html")
        self.assertIn('unit_testing_tag', str(req.data))

    # TODO: looks like admin flag is not working
    def test_tags_page(self):
        """elevate user to admin and verify you can edit the tags page"""
        # set the session
        self._set_session(True)
        # elevate user to admin
        self._switch_admin(True)
        #self.test_get_sample()
        req = self._client.get("tag/unit_testing_tag.html")
        self.assertIn(self._edit_samples_button, str(req.data))
        # demote user
        self._switch_admin()

    def test_get_sample(self):
        """see if the test sample exists"""
        db = mdb.get_db()
        sample = db.samples.find_one({'sample_id': "unit_tester"})
        if sample:
            print("sample id: {}, visibility: {}, owner: {}".format(sample['_id'], sample['is_public'], sample['owner']))
        else:
            print("no test sample found!")