import json
import os
import sys

import utils.constants as cn


class Config:
    def __init__(self):
        self.file = cn.CONFIG_FILE
        self.default_conf = json.loads(self._read_text('default_config.json'))

    def _generate_conf(self):
        if not os.path.isfile(self.file):
            with open(self.file, 'w') as outfile:
                self._write_json(self.default_conf, outfile)
        with open(self.file, 'r+') as json_file:
            data = json.load(json_file)
            for key in self.default_conf:
                if key not in data:
                    data[key] = self.default_conf[key]
            self._write_json(data, json_file)

    def read_conf(self):
        class ConfigUsable(object):
            pass

        # if not os.path.exists(self.file):
        self._generate_conf()

        conf = ConfigUsable()
        try:
            with open(self.file, 'r') as json_file:
                data = json.load(json_file)
                for key in data:
                    setattr(conf, key, data[key])
            return conf
        except json.decoder.JSONDecodeError:
            sys.exit('Failed to read the config file!')

    @staticmethod
    def _write_json(data, json_file):
        json_file.seek(0)
        json.dump(data, json_file, indent=4)
        json_file.truncate()

    @staticmethod
    def _read_text(path):
        if not os.path.isfile(path):
            return None
        file = open(path)
        text = file.read()
        file.close()
        return text


cfg = Config.read_conf(Config())
