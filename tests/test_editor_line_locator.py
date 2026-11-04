import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 't18d-8255-debug/scripts/editor_line_locator.py'
spec = importlib.util.spec_from_file_location('locator', SCRIPT)
locator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locator)

class EditorLinesTest(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(__file__).resolve().parent / ('.scratch-' + uuid.uuid4().hex)
        self.scratch.mkdir()
        self.path = self.scratch / 'input.log'

    def tearDown(self):
        if self.scratch.resolve().parent != Path(__file__).resolve().parent:
            raise RuntimeError('Unexpected scratch directory')
        shutil.rmtree(self.scratch)

    def test_mixed_newlines_blank_and_unicode(self):
        self.path.write_bytes('首行\r\n\n目标一\r目标二\u2028同一行\n尾行'.encode('utf-8'))
        self.assertEqual(list(locator.iter_editor_lines(self.path)), [(1,'首行'), (2,''), (3,'目标一'), (4,'目标二\u2028同一行'), (5,'尾行')])

    def test_encodings(self):
        for encoding in ('utf-8-sig', 'utf-16', 'gb18030'):
            with self.subTest(encoding=encoding):
                self.path.write_bytes('中文\r目标\n结束'.encode(encoding))
                self.assertEqual(locator.locate(self.path, needle='目标', encoding=encoding)['matches'], [{'editor_line':2, 'text':'目标'}])

    def test_gzip_and_cli(self):
        self.path.write_bytes(gzip.compress(b'A\rB\r\nC\n'))
        output = subprocess.check_output([sys.executable, '-X', 'utf8', '-B', str(SCRIPT), str(self.path), '--text', 'B'], encoding='utf-8')
        self.assertEqual(json.loads(output)['matches'], [{'editor_line':2, 'text':'B'}])

    def test_repeated_matches_and_line(self):
        self.path.write_bytes(b'A\rA\nA')
        limited = locator.locate(self.path, needle='A', max_hits=2)
        self.assertTrue(limited['more_matches'])
        self.assertEqual([m['editor_line'] for m in limited['matches']], [1,2])
        self.assertEqual(locator.locate(self.path, line=3)['matches'], [{'editor_line':3,'text':'A'}])
        self.assertEqual(locator.locate(self.path, line=4)['matches'], [])

    def test_boundary_empty_and_trailing_newlines(self):
        for content, expected in ((b'', []), (b'\r\n\r\n', ['', '']), (b'A\r\nB\nC\rD\r\n', ['A','B','C','D']), (b'X'*8191 + b'\r\nY', ['X'*8191,'Y'])):
            with self.subTest(length=len(content)):
                self.path.write_bytes(content)
                self.assertEqual([text for _, text in locator.iter_editor_lines(self.path)], expected)

    def test_read_only(self):
        self.path.write_bytes(b'A\rB\nC')
        before = hashlib.sha256(self.path.read_bytes()).digest()
        locator.locate(self.path, needle='B')
        self.assertEqual(before, hashlib.sha256(self.path.read_bytes()).digest())

    def test_invalid_encoding_fails(self):
        self.path.write_bytes(b'\xff\xfe\xff')
        with self.assertRaises(UnicodeError):
            list(locator.iter_editor_lines(self.path))

    def test_invalid_cli_line_fails(self):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), str(self.path), '--line', '0'], capture_output=True)
        self.assertEqual(result.returncode, 2)

if __name__ == '__main__':
    unittest.main()
