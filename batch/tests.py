"""
    OCR batch tests.
"""
import os
import re
import shutil
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import simplejson


TESTFILE = "simple.png"


class OcrBatchTest(TestCase):
    fixtures = ["ocrmodels/fixtures/test_fixtures.json",
            "projects/fixtures/test_fixtures.json"]

    def setUp(self):
        """
            Setup OCR tests.  Creates a test user.
        """
        shutil.copy2("media/models/mytessdata.tgz", "media/test/engtessdata.tgz")
        shutil.copy2("media/models/default.model", "media/test/default.model")
        shutil.copy2("media/models/default.fst", "media/test/default.fst")
        os.makedirs("media/files/test_user/test")
        shutil.copy2("media/test/%s" % TESTFILE, "media/files/test_user/test/%s" % TESTFILE)
        self.testuser = User.objects.create_user("test_user", "test@testing.com", "testpass")
        self.client = Client()
        self.client.login(username="test_user", password="testpass")
        self.client.get("/projects/load/1/")


    def tearDown(self):
        """
            Cleanup a test.
        """
        self.testuser.delete()
        shutil.rmtree("media/files/test_user")


    def test_batch_new(self):
        """
        Test the convert view as a standard GET (no processing.)
        """
        self.assertEqual(self.client.get("/batch/new").status_code, 200)


    def test_batch_create(self):
        """
        Test OCRing with minimal parameters.
        """
        self._test_batch_action()        


    def test_results_action(self):
        """
        Test fetching task results.  Assume a batch with pk 1
        exists.
        """
        pk = self._test_batch_action()        
        r = self.client.get("/batch/results/%s" % pk)
        self.assert_(r.content, "No content returned")
        content = simplejson.loads(r.content)
        self.assertEqual(
                content[0]["fields"]["tasks"][0]["fields"]["page_name"], 
                os.path.basename(TESTFILE))
        return pk


    def test_page_results_page_action(self):
        """
        Test fetching task results.  Assume a page with offset 0
        exists.
        """
        pk = self._test_batch_action()        
        r = self.client.get("/batch/results/%s/0/" % pk)
        self.assert_(r.content, "No content returned")
        content = simplejson.loads(r.content)
        self.assertEqual(
                content[0]["fields"]["page_name"], 
                os.path.basename(TESTFILE))


    def test_save_transcript(self):
        """
        Test fetching task results.  Assume a page with offset 0
        exists.
        """
        pk = self._test_batch_action()        
        r = self.client.get("/batch/results/%s/0/" % pk)
        self.assert_(r.content, "No content returned")
        content = simplejson.loads(r.content)
        self.assertEqual(
                content[0]["fields"]["page_name"], 
                os.path.basename(TESTFILE))


    def test_transcript_action(self):
        """
        Test viewing the transcript for a new batch.
        """
        pk = self._test_batch_action()        
        r = self.client.get("/batch/transcript/%s/" % pk)
        self.assertEqual(r.status_code, 200)


    def test_show_action(self):
        """
        Test viewing batch details.
        """
        pk = self._test_batch_action()        
        r = self.client.get("/batch/show/%s/" % pk)
        self.assertEqual(r.status_code, 200)


    def _test_batch_action(self, params=None, headers={}):
        """
        Testing actually OCRing a file.
        """
        if params is None:
            params = dict(name="Test Batch", 
                    files=os.path.join("test/%s" % TESTFILE))
        r = self._get_batch_response(params, headers)
        # check the POST redirected as it should
        self.assertEqual(r.redirect_chain[0][1], 302)
        pkmatch = re.match(".+/batch/show/(\d+)/?", r.redirect_chain[0][0])
        self.assertTrue(pkmatch != None)        
        return pkmatch.groups()[0]


    def test_file_upload(self):
        """
        Test uploading files to the server.
        """
        upload = os.path.join(settings.MEDIA_ROOT, "test", TESTFILE)
        fh = file(upload, "rb")
        params = {}
        params["file1"] = fh
        headers = {}
        r = self.client.post("/batch/upload_files/", params, **headers)
        fh.close()
        content = simplejson.loads(r.content)
        self.assertEqual(content, [os.path.join("test-project-2", TESTFILE)])
      

    def _get_batch_response(self, params={}, headers={}):
        """
        Post images for conversion with the given params, headers.
        """
        headers["follow"] = True
        return self.client.post("/batch/create/", params, **headers)
        

