import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import cs
import download_course as course


class UpdateTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path(__file__).resolve().parents[1] / 'private/test-tmp'
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temp_root)
        self.root = Path(self.temp.name)
        self.patches = [patch.object(course, 'ROOT', self.root),
                        patch.object(course, 'DEST', self.root / 'materials/fa26'),
                        patch.object(course, 'PRIVATE', self.root / 'private/answers/fa26')]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def archive(self, name, content):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr(name, content)
        return stream.getvalue()

    def test_preserves_exercise_and_saves_official_update(self):
        folder = course.DEST / 'hw/hw01'
        target = folder / 'code/hw01.py'
        course.save(target, b'my solution')
        _, kept = cs.extract_starter(course, self.archive('hw01/hw01.py', b'new starter'), folder, 'hw01')
        self.assertEqual(target.read_bytes(), b'my solution')
        self.assertEqual(len(kept), 1)
        self.assertEqual(next((self.root / 'private/upstream').rglob('hw01.py')).read_bytes(), b'new starter')

    def test_blocks_archive_traversal(self):
        with self.assertRaises(ValueError):
            cs.extract_starter(course, self.archive('../escape.py', b'bad'), course.DEST, 'hw01')
        self.assertFalse((self.root / 'escape.py').exists())

    def test_generated_update_retains_previous_bytes(self):
        target = course.DEST / 'manifest.json'
        course.save(target, b'old')
        course.replace_generated(target, b'new')
        self.assertEqual(target.read_bytes(), b'new')
        self.assertEqual(next((self.root / 'private/update-backups').rglob('manifest.json')).read_bytes(), b'old')

    def test_refresh_uses_network_instead_of_stale_cache(self):
        import hashlib
        url = 'https://cs61a.org/fa26/'
        cache = self.root / 'private/download-cache' / hashlib.sha256(url.encode()).hexdigest()
        course.save(cache, b'old homepage')
        with patch.object(course, 'REFRESH', True), patch.object(course, 'FETCHED', {}), patch.object(course, 'urlopen', return_value=io.BytesIO(b'new homepage')) as network:
            self.assertEqual(course.fetch(url), b'new homepage')
            self.assertEqual(course.fetch(url), b'new homepage')
            self.assertEqual(network.call_count, 1)
        self.assertEqual(cache.read_bytes(), b'new homepage')

    def test_partial_failure_preserves_previous_record(self):
        url = course.BASE + 'hw/hw01/'
        record = dict(url=url, kind='hw', title='old', pdf='materials/fa26/hw/hw01/hw01.pdf')
        path = course.DEST / 'manifest.json'
        course.save(path, json.dumps({'records': [record]}).encode())
        with patch.object(course, 'fetch', return_value=b'homepage'), patch.object(cs, 'discover', return_value={url:'hw'}), patch.object(cs, 'update_item', side_effect=OSError('offline')):
            self.assertEqual(cs.update(course), 1)
        payload = json.loads(path.read_text())
        self.assertEqual(payload['records'], [record])
        self.assertEqual(len(payload['failures']), 1)


if __name__ == '__main__':
    unittest.main()
