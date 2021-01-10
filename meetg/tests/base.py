import logging, unittest

import settings
from meetg.utils import import_string


class BaseTestCase(unittest.TestCase):

    def _drop_db(self):
        for model_class in settings.model_classes:
            Model = import_string(model_class)
            Model(test=True).drop()

    def setUp(self):
        super().setUp()
        settings.db_name_test = 'MeeTgTestDB'
        settings.log_level = logging.WARNING
        self._drop_db()

    def tearDown(self):
        super().tearDown()
        self._drop_db()
