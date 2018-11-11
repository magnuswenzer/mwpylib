import os
import json


class User(object):
    def __init__(self, settings_path):
        self.settings_path = settings_path




class UserSettings(object):
    """
    Baseclass for user settings.
    """
    def __init__(self, directory, settings_type):
        self.directory = directory
        self.settings_type = settings_type
        self.file_path = os.path.join(self.directory, '{}.json'.format(self.settings_type))

        self.data = {}

        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

        if not os.path.exists(self.file_path):
            self._save()

        self._load()

    def _load(self):
        """
        Loads dict from json
        :return:
        """
        if os.path.exists(self.file_path):
            with open(self.file_path) as fid:
                self.data = json.load(fid)

    def _save(self):
        """
        Writes information to json file.
        :return:
        """
        with open(self.file_path, 'w') as fid:
            json.dump(self.data, fid)


    def setdefault(self, key, value):
        pass
