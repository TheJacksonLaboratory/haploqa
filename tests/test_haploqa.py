import unittest
import haploqa.haploqaapp as hqa
import haploqa.mongods as mdb
from bson import ObjectId
import os
import distutils.dir_util as dir_util
from zipfile import BadZipFile
import logging

logging.basicConfig(level=logging.INFO)


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
        logging.debug("Setup: Created test user {}".format(uid))
        # find a private sample not owned by the test user
        sample = db.samples.find_one({'sample_id': "32C"})
        sample2 = sample
        sample_id = ObjectId()
        logging.debug("Setup: test sample id is {}".format(sample_id))
        sample2['_id'] = sample_id
        #make the id available to the tests
        cls._sample_id = sample_id
        sample2['sample_id'] = 'unit_tester'
        sample2['tags'] = ["unit_testing_tag"]
        sample2['is_public'] = True
        sample2['owner'] = tester_email
        db.samples.insert_one(sample2)
        logging.debug("Setup: creating test client")
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
        logging.debug("Teardown: removed test sample")
        cls._db.users.delete_one({"email_address_lowercase": cls._tester_email})
        logging.debug("Teardown: removed test user")

    def setUp(self):
        # clear the session
        self._set_session()

    def tearDown(self):
        #clear the session and reset test user priviliges
        self._set_session()
        self._switch_admin()
        # reset the sample back to its default state
        self._switch_sample(True, self._tester_email)

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
            # set to 127.0.0.1 if testing locally
            sess['remote_addr'] = None

    def _switch_sample(self, public=True, owner=None):
        """
        switch test sample public / private or owner
        :param public: True / False
        :param owner: null or owner email
        :return:
        """

        self._db.samples.update_one(
            {"_id": self._sample_id},
            {"$set":
                {
                    "is_public": public,
                    "owner": owner
                }
            })

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
                    "administrator": admin,
                    "std_des_admin": True
                },
            })

    ### Unit Tests ###

    def test_home_page(self):
        """ test the home page as unauthenticated user"""

        req = self._client.get("tag/GigaMUGA.html")
        self.assertEqual(req.status, '200 OK')

    def test_private_sample(self):
        """hit private sample and verify it can't be viewed by an unauthenicated user"""
        # make sample private
        self._switch_sample(False)
        req = self._client.get("sample/{}.html".format(self._sample_id))
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
        # make sample private
        self._switch_sample(False)
        req = self._client.get("sample/{}.html".format(self._sample_id))
        # make sure you have an active session and can view the page
        self.assertNotIn('Login Required', str(req.data))
        # make sure that you get the sample page but not the edit button
        self.assertNotIn(self._edit_sample_button, str(req.data))

    def test_private_sample(self):
        """verify the regular user can see the sample tag on, but not edit the tags page"""

        # hit the tags page - the sample should not be there
        req = self._client.get("tag/unit_testing_tag.html")
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
        # set owner of sample to other than the tester
        self._switch_sample(False, 'not@tester.com')
        req = self._client.get("sample/{}.html".format(self._sample_id))
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
        # set owner of sample to other than the tester
        self._switch_sample(False, 'not@tester.com')
        req = self._client.get("sample/{}.html".format(self._sample_id))
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

    def test_std_des_admin(self):
        """test permissions on standard designation admin page"""

        # hit page w/o login
        req = self._client.get("strain-name-admin.html")
        # verify the login required message
        self.assertIn('Login Required', str(req.data))
        # hit page with regular login
        self._set_session(False, self._tester_email)
        req = self._client.get("strain-name-admin.html")
        self.assertIn('Login Required', str(req.data))
        # update user to st-des-admin
        self._switch_admin(True)
        req = self._client.get("strain-name-admin.html")
        # verify you can see the page
        self.assertIn('Standard Designations', str(req.data))


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
            logging.debug("sample id: {}, visibility: {}, owner: {}"
                          .format(sample['_id'], sample['is_public'], sample['owner']))
        else:
            logging.debug("no test sample found!")


class TestZipFileExtraction(unittest.TestCase):
    TEMP_DIR = 'tests/data/'
    TEST_DATA_DIR = 'tests/test_files/'

    @classmethod
    def setUpClass(cls):
        """
        Since the zip file extraction function assumes the zip file is already
        saved, should try to extract the zip file content, rename the content and
        remove the original file, we don't want to lose the static testing files,
        so prior to all of the tests, make a complete copy of the testing files
        :return:
        """
        temp_dir = TestZipFileExtraction.TEMP_DIR
        test_data_dir = TestZipFileExtraction.TEST_DATA_DIR

        if not os.path.exists(temp_dir):
            logging.debug("Creating temp directory")
            # make a temp directory with a copy of the static test files
            os.makedirs(temp_dir)
            if os.path.exists(temp_dir):
                logging.debug("Temp directory exists")
            else:
                logging.debug("Temp directory is missing")
            if os.path.exists(test_data_dir):
                logging.debug("Copying test files into temp directory")
                dir_util.copy_tree(test_data_dir, temp_dir)

    @classmethod
    def tearDownClass(cls):
        """
        Remove the testing temp directory and all of its contents at the end of
        the test running
        :return:
        """
        temp_dir = TestZipFileExtraction.TEMP_DIR
        if os.path.exists(temp_dir):
            logging.debug("Removing temp directory")
            # remove the temp directory and all of the contents
            dir_util.remove_tree(temp_dir)

    def test_good_zip(self):
        """
        Tests that a valid zip file with a single text file as content can be
        extracted and the zip file that is extracted from gets removed
        :return:
        """
        temp_dir = TestZipFileExtraction.TEMP_DIR
        hqa.extract_zip_file("{}good.zip".format(temp_dir),
                             "{}good_result".format(temp_dir),
                             temp_dir)

        # check that extracted file exists and is named as specified
        self.assertTrue(os.path.exists("{}good_result".format(temp_dir)))
        # check that zip file has been removed
        self.assertFalse(os.path.exists("{}good.zip".format(temp_dir)))

    def test_nonexistent_file(self):
        """
        Tests that an incorrect filename that the function looks for triggers a
        FileNotFoundError with the proper message
        :return:
        """
        temp_dir = TestZipFileExtraction.TEMP_DIR

        with self.assertRaises(FileNotFoundError) as context:
            hqa.extract_zip_file("{}nonexistent.zip".format(temp_dir),
                                 "{}nonexistent".format(temp_dir),
                                 temp_dir)

            self.assertTrue('OOPS! We seem to have misplaced the zip file'
                            in context.exception)

    def test_empty_zip(self):
        """
        Tests that an empty zip file triggers a Exception with the proper message
        :return:
        """
        temp_dir = TestZipFileExtraction.TEMP_DIR

        with self.assertRaises(Exception) as context:
            hqa.extract_zip_file("{}empty.zip".format(temp_dir),
                                 "{}empty_result".format(temp_dir),
                                 temp_dir)

            self.assertTrue('Somehow the zip is empty' in context.exception)

    def test_fake_zip(self):
        """
        Tests that a fake zip file (a non-zip file but with a changed extension
        to .zip) triggers a BadZipFile error
        :return:
        """
        temp_dir = TestZipFileExtraction.TEMP_DIR

        with self.assertRaises(BadZipFile):
            hqa.extract_zip_file("{}fake.zip".format(temp_dir),
                                 "{}fake_result".format(temp_dir),
                                 temp_dir)

    def test_file_not_zip(self):
        """
        Tests that a txt file triggers a BadZipFile error
        :return:
        """
        temp_dir = TestZipFileExtraction.TEMP_DIR

        with self.assertRaises(BadZipFile):
            hqa.extract_zip_file("{}not_zip.txt".format(temp_dir),
                                 "{}not_zip".format(temp_dir),
                                 temp_dir)

    def test_zip_content_not_txt(self):
        """
        Tests that a zip file that contains a file that isn't a .txt file
        triggers a Exception with the proper message
        :return:
        """
        temp_dir = TestZipFileExtraction.TEMP_DIR

        with self.assertRaises(Exception) as context:
            hqa.extract_zip_file("{}file_not_txt.zip".format(temp_dir),
                                 "{}not_text".format(temp_dir),
                                 temp_dir)

            self.assertTrue('The file in the zip file needs to be a .txt'
                            in context.exception)

    def test_zip_contains_multiple_txts(self):
        """
        Tests that a zip file that contains a file that isn't a .txt file
        triggers a Exception with the proper message
        :return:
        """
        temp_dir = TestZipFileExtraction.TEMP_DIR

        with self.assertRaises(Exception) as context:
            hqa.extract_zip_file("{}2_txts.zip".format(temp_dir),
                                 "{}2_txts".format(temp_dir),
                                 temp_dir)

            self.assertTrue('The zip file needs to only contain 1 file but 2 were found'
                            in context.exception)
