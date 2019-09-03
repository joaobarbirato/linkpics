"""
    Stanford CoreNLP function wrapper
    @author: João Gabriel Melo Barbirato
"""

import subprocess
from time import sleep

from config import TMP_DIR, BASE_DIR, CORENLP_DIR

_UTIL_SHELL_BASE = '/app/src/UTIL/shell'

_dict_commands = {
    'start_base': '/usr/bin/bash ' + BASE_DIR + _UTIL_SHELL_BASE + '/start-corenlp-server.sh '
                  + BASE_DIR + '/' + CORENLP_DIR + ' ' + TMP_DIR,
    'stop_base': '/usr/bin/bash ' + BASE_DIR + _UTIL_SHELL_BASE + '/stop-corenlp-server.sh ' + TMP_DIR,
    'correference_resolution': f'/usr/bin/bash {BASE_DIR}/{_UTIL_SHELL_BASE}/coreference-corenlp.sh {BASE_DIR}/{CORENLP_DIR}'
}


class CoreNLPWrapper:
    def __init__(self):
        self._subprocess = None
        self.corefs_dict = {}

    def communicate(self):
        if self._subprocess is not None:
            self._subprocess.communicate()

    def start_base(self):
        self._subprocess = subprocess.Popen(_dict_commands['start_base'].split(' '))
        sleep(1)

    def _get_coref_from_xml(self, file_name='coref_input', out_dir=TMP_DIR):
        import xml.etree.ElementTree as ET
        print(f'{out_dir}/{file_name}')
        tree = ET.parse(f'{out_dir}/{file_name}.xml')
        root = tree.getroot()

        # find coref key
        corefs = root.find('document').find('coreference')
        snts = root.find('document').find('sentences')

        self.corefs_dict['tokenized'] = [[tkn.find('word').text for tkn in snt.find('tokens').findall('token')] for snt in snts.findall('sentence')]

        for coref in corefs:
            print(f'Coreference {corefs}')
            self.corefs_dict[coref] = {}
            for mention in coref:
                self.corefs_dict[coref][mention] = {}
                print(f'\tMention {mention}')
                for item in mention:
                    self.corefs_dict[coref][mention][item.tag] = item.text
                    print(f'\t\titem[{item.tag}] = {item.text}')

        return self.corefs_dict

    def coreference_resolution(self, sentences=None, out_dir=TMP_DIR, comm=True):
        """
        Coreference resolution
        :param sentences: sentence list
        :param out_dir: output directory
        :param comm: conditional for waiting on the subprocess to end
        :return:
        """
        if sentences is None:
            return

        input_path = f'{TMP_DIR}/coref_input'
        print(input_path)
        with open(input_path, 'w') as input_file:
            if isinstance(sentences, list):
                input_file.write('. '.join(sentences))
            elif isinstance(sentences, str):
                input_file.write(sentences)

        command_with_args = f'{_dict_commands["correference_resolution"]} {input_path} {out_dir}'
        self._subprocess = subprocess.Popen(command_with_args.split(' '))
        if comm:
            self._subprocess.communicate()

        self.corefs_dict = self._get_coref_from_xml()


        return self.corefs_dict

    def terminate_base(self):
        self._subprocess = subprocess.Popen(_dict_commands['stop_base'].split(' '))
        sleep(1)


if __name__ == "__main__":
    cnlpw = CoreNLPWrapper()
    cnlpw.coreference_resolution(
        sentences=[
            'John likes to punch himself in the face',
            'On the other hand, Jake Peralta was arguing with Amy Santiago that he could wash their dishes better'
            ' than her'],
        out_dir='app/tmp'
    )