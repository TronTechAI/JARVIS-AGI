"""Execute exact pinned main.py with a synthetic IMPORTS boundary; stdlib only."""
import concurrent.futures
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(os.environ.get('JARVIS_TEST_SOURCE_ROOT', str(REPO)))
SOURCE = SOURCE_ROOT / 'main.py'
HISTORY_PATH = SOURCE_ROOT / 'TOOLS/Alpaca_DS_Converser.py'
History = runpy.run_path(str(HISTORY_PATH), run_name='synthetic_history')['ConversationHistoryManager']
HISTORY_GLOBALS = History.__init__.__globals__
RUNTIME = tempfile.TemporaryDirectory(prefix='jarvis-history-tests-')
ROOT = Path(RUNTIME.name)
(ROOT / 'runtime-data').mkdir()

def prohibit_live(event, args):
    if event.startswith('socket.') or event in ('subprocess.Popen', 'os.system'):
        raise AssertionError('Live operation prohibited: ' + event)

sys.addaudithook(prohibit_live)

class EndFixture(BaseException):
    pass

class Fixture:
    def __init__(self, speech, classifier='ordinary', image='no', failure=None):
        self.root = Path(tempfile.mkdtemp(prefix='synthetic-', dir=ROOT / 'runtime-data'))
        self.history = History(str(self.root / 'history.json'))
        self.inputs = iter(speech)
        self.spoken, self.requests, self.executors = [], [], []
        self.listen_calls = 0
        self.image_path = self.root / 'synthetic-image.txt'
        self.image_path.write_text('synthetic pixels; no image or camera data')
        self.removed, self.website_calls, self.image_calls = [], [], []
        self.error = None
        self.failure = failure
        self.system_calls = []
        outer = self
        class Executor(concurrent.futures.ThreadPoolExecutor):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.entered = self.exited = False
                outer.executors.append(self)
            def __enter__(self):
                self.entered = True
                return super().__enter__()
            def __exit__(self, *args):
                result = super().__exit__(*args)
                self.exited = True
                return result
        def listen():
            self.listen_calls += 1
            try:
                return next(self.inputs)
            except StopIteration:
                raise EndFixture()
        def generate(history, system_prompt, **kwargs):
            self.requests.append((system_prompt, copy.deepcopy(history)))
            if failure == 'classifier' and system_prompt == 'classifier':
                raise RuntimeError('synthetic classifier failure')
            return {'image': image, 'classifier': classifier, 'default': 'synthetic answer'}[system_prompt]
        def speak(text, **kwargs):
            self.spoken.append((text, kwargs))
        def image_generate(query):
            self.image_calls.append(query)
            if failure == 'image': raise RuntimeError('synthetic image failure')
        def camera():
            if failure == 'camera': raise RuntimeError('synthetic camera failure')
            return str(self.image_path)
        def vision(*args, **kwargs):
            if failure == 'vision': raise RuntimeError('synthetic vision failure')
            return 'synthetic vision answer'
        def remove(path):
            assert Path(path) == self.image_path
            self.removed.append(path)
            os.remove(path)
        def url():
            if failure == 'url': raise RuntimeError('synthetic URL failure')
            return 'https://synthetic.invalid/'
        def website(url):
            self.website_calls.append(url)
            if failure == 'website': raise RuntimeError('synthetic website failure')
            return 'synthetic site'
        def web_generate(*args, **kwargs):
            if failure == 'web_generate': raise RuntimeError('synthetic web generation failure')
            return 'synthetic website answer'
        ns = types.SimpleNamespace
        self.module = types.ModuleType('IMPORTS')
        self.module.__dict__.update(listener=ns(listen=listen), history_manager=self.history,
            concurrent=ns(futures=ns(ThreadPoolExecutor=Executor, wait=concurrent.futures.wait)),
            deepInfra_TEXT=ns(generate=generate), BISECTORS=ns(image_requests_v3='image', complex_task_classifier_v6='classifier'),
            INSTRUCTIONS=ns(human_response_v3_AVA='default', vison_realtime_v1='vision'),
            speak=speak, decohere_ai=ns(generate=image_generate), camera_vision=ns(realtime_vision=camera),
            deepInfra_VISION=ns(generate=vision), os=ns(path=os.path, remove=remove),
            chrome_latest_url=ns(get_latest_chrome_url=url), jenna_reader=ns(fetch_website_content=website),
            openrouter=ns(generate=web_generate), Hugging_Face_TEXT=ns(generate=lambda _: 'synthetic ordinary answer'),
            system_theme=ns(WindowsThemeManager=lambda: ns(set_theme=lambda value: self.system_calls.append(value))))
    def run(self):
        assert 'IMPORTS' not in sys.modules
        sys.modules['IMPORTS'] = self.module
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                try: exec(compile(SOURCE.read_bytes(), str(SOURCE), 'exec'), {'__name__': 'synthetic_main'})
                except EndFixture: pass
                except Exception as error: self.error = error
        finally:
            del sys.modules['IMPORTS']
            # Drain original-source unmanaged executors as test teardown only.
            for executor in self.executors: executor.shutdown(wait=True)
        return self

class Qualification(unittest.TestCase):
    def completed(self, f):
        self.assertIsNone(f.error)
        self.assertTrue(f.executors)
        self.assertTrue(all(e.entered and e.exited for e in f.executors))
        self.assertTrue(all(not t.is_alive() for e in f.executors for t in e._threads))
    def test_prefix_history_and_persistence(self):
        f=Fixture(['JaRvIs explain stars']).run(); self.completed(f)
        expected=[{'role':'user','content':'explain stars'},{'role':'assistant','content':'synthetic answer'}]
        self.assertEqual(f.history.history, expected)
        self.assertEqual(json.loads(Path(f.history.conversation_file).read_text()),expected)
        self.assertEqual([r for key,r in f.requests if key=='default'], [expected[:1]])
    def test_suffix_and_second_turn_context(self):
        f=Fixture(['explain stars JARVIS','jarvis explain moons']).run(); self.completed(f)
        calls=[r for key,r in f.requests if key=='default']
        self.assertEqual(calls[0],[{'role':'user','content':'explain stars'}])
        self.assertEqual(calls[1], [{'role':'user','content':'explain stars'},{'role':'assistant','content':'synthetic answer'},{'role':'user','content':'explain moons'}])
        self.assertEqual(History(f.history.conversation_file).history,f.history.history)
    def test_ambiguous_classifier_persists_fallback(self):
        f=Fixture(['jarvis hello'],classifier='vision website call youtube').run(); self.completed(f)
        self.assertEqual(len(json.loads(Path(f.history.conversation_file).read_text())),2)
        self.assertEqual(len(f.history.history),2)
    def test_image_failure_returns_to_listen(self):
        f=Fixture(['jarvis draw a tree'],image='yes',failure='image').run(); self.completed(f)
        self.assertEqual(f.image_calls,['draw a tree'])
        self.assertEqual(f.listen_calls,2)
        self.assertIn('Sorry Sir, I was unable to generate the image.', [x[0] for x in f.spoken])
    def test_vision_success_removes_only_synthetic_file(self):
        f=Fixture(['jarvis look'],classifier='vision').run(); self.completed(f)
        self.assertEqual(f.removed,[str(f.image_path)])
        self.assertFalse(f.image_path.exists())
        self.assertIn('synthetic vision answer',[x[0] for x in f.spoken])
    def test_vision_failure_cleans_up_and_continues(self):
        f=Fixture(['jarvis look'],classifier='vision',failure='vision').run(); self.completed(f)
        self.assertFalse(f.image_path.exists()); self.assertEqual(f.listen_calls,2)
        self.assertIn('Sorry Sir, I was unable to analyse the image.',[x[0] for x in f.spoken])
    def test_website_success(self):
        f=Fixture(['jarvis summarize'],classifier='website').run(); self.completed(f)
        self.assertEqual(f.website_calls,['https://synthetic.invalid/'])
        self.assertIn(('synthetic website answer',{'voice':'Salli'}),f.spoken)
    def test_website_failure_boundaries_continue(self):
        for failure in ['url','website','web_generate']:
            with self.subTest(failure=failure):
                f=Fixture(['jarvis summarize'],classifier='website',failure=failure).run(); self.completed(f)
                self.assertEqual(f.listen_calls,2)
                self.assertIn('Sorry Sir, I was unable to fetch the website content.',[x[0] for x in f.spoken])
    def test_non_wake_ordinary_history_unchanged(self):
        f=Fixture(['hello']).run()
        self.assertIsNone(f.error); self.assertEqual(f.executors,[])
        self.assertEqual(f.history.history,[{'role':'user','content':'hello'},{'role':'assistant','content':'synthetic ordinary answer'}])
    def test_characterize_unhandled_camera_failure(self):
        f=Fixture(['jarvis look'],classifier='vision',failure='camera').run()
        self.assertIsInstance(f.error,RuntimeError);self.assertEqual(f.listen_calls,1)
    def test_characterize_unhandled_classifier_failure(self):
        f=Fixture(['jarvis hello'],failure='classifier').run()
        self.assertIsInstance(f.error,RuntimeError);self.assertEqual(f.listen_calls,1)

class ActionHistory(unittest.TestCase):
    def assert_empty(self, f):
        self.assertEqual(f.history.history, [])
        self.assertFalse(Path(f.history.conversation_file).exists())
    def continue_conversation(self, f):
        f.inputs = iter(['jarvis explain stars'])
        seen = []
        def generate(history, system_prompt, **kwargs):
            if system_prompt == 'default':
                seen.append(copy.deepcopy(history))
                # Model the actual provider's list/dict mutation without importing it.
                history.insert(0, {'role':'system','content':'synthetic prompt'})
                history[-1]['content'] = 'mutated request only'
            return {'image':'no','classifier':'ordinary','default':'synthetic answer'}[system_prompt]
        f.module.deepInfra_TEXT.generate = generate
        f.run()
        self.assertIsNone(f.error)
        self.assertEqual(seen, [[{'role':'user','content':'explain stars'}]])
        expected = [{'role':'user','content':'explain stars'}, {'role':'assistant','content':'synthetic answer'}]
        self.assertEqual(f.history.history, expected)
        self.assertEqual(json.loads(Path(f.history.conversation_file).read_text()), expected)
        self.assertEqual(History(f.history.conversation_file).history, expected)
    def test_successful_image_then_conversation_then_reload(self):
        f=Fixture(['jarvis draw a tree'], image='yes').run()
        self.assertIsNone(f.error); self.assertEqual(f.image_calls, ['draw a tree'])
        self.assert_empty(f); self.continue_conversation(f)
    def test_failed_image_then_conversation_then_reload(self):
        f=Fixture(['jarvis draw a tree'], image='yes', failure='image').run()
        self.assertIsNone(f.error); self.assert_empty(f); self.continue_conversation(f)
    def test_action_branches_leave_history_unchanged(self):
        cases=[('vision',None),('vision','vision'),('website',None),('website','website'),('call',None),('system control',None)]
        for classifier, failure in cases:
            with self.subTest(classifier=classifier, failure=failure):
                f=Fixture(['jarvis dark'],classifier=classifier,failure=failure).run()
                self.assertIsNone(f.error); self.assert_empty(f)
    def test_action_preserves_prior_committed_pair_despite_provider_mutation(self):
        f=Fixture(['hello']).run()
        before=copy.deepcopy(f.history.history); disk=Path(f.history.conversation_file).read_bytes()
        f.inputs=iter(['jarvis call'])
        def generate(history,system_prompt,**kwargs):
            if system_prompt=='default':
                history.insert(0,{'role':'system','content':'synthetic'})
                history[1]['content']='mutation must stay private'
            return {'image':'no','classifier':'call','default':'unused answer'}[system_prompt]
        f.module.deepInfra_TEXT.generate=generate; f.run()
        self.assertIsNone(f.error); self.assertEqual(f.history.history,before)
        self.assertEqual(Path(f.history.conversation_file).read_bytes(),disk)
    def test_failed_conversation_save_preserves_state_then_next_turn_succeeds(self):
        f=Fixture(['hello']).run(); before=copy.deepcopy(f.history.history)
        disk=Path(f.history.conversation_file).read_bytes(); f.inputs=iter(['jarvis unsaved question'])
        # Original source has no atomic replace path: it will incorrectly commit.
        with mock.patch.object(HISTORY_GLOBALS['os'], 'replace', side_effect=OSError('synthetic save failure')):
            f.run()
        self.assertIsNone(f.error); self.assertEqual(f.history.history,before)
        self.assertEqual(Path(f.history.conversation_file).read_bytes(),disk)
        f.inputs=iter(['jarvis saved question']); f.run(); self.assertIsNone(f.error)
        expected=before+[{'role':'user','content':'saved question'},{'role':'assistant','content':'synthetic answer'}]
        self.assertEqual(f.history.history,expected)
        self.assertEqual(History(f.history.conversation_file).history,expected)
    def test_failed_first_save_does_not_create_history_or_leave_pending_user(self):
        f=Fixture(['jarvis unsaved question'])
        with mock.patch.object(HISTORY_GLOBALS['os'], 'replace', side_effect=OSError('synthetic save failure')):
            f.run()
        self.assertIsNone(f.error); self.assert_empty(f)


class Persistence(unittest.TestCase):
    def history(self):
        root=Path(tempfile.mkdtemp(dir=ROOT/'runtime-data')); path=root/'history.json'
        initial=[{'role':'user','content':'before'},{'role':'assistant','content':'answer'}]
        path.write_text(json.dumps(initial)); return History(str(path)), path, initial
    def test_serialization_failure_preserves_file_and_ram(self):
        h,path,initial=self.history(); before=path.read_bytes()
        def broken_dump(data, file, **kwargs):
            file.write('partial output'); raise OSError('synthetic write failure')
        with mock.patch.object(HISTORY_GLOBALS['json'],'dump',side_effect=broken_dump):
            with self.assertRaises(OSError): h.record_turn('next','response')
        self.assertEqual(path.read_bytes(),before); self.assertEqual(h.history,initial)
        self.assertEqual(list(path.parent.iterdir()),[path])
    def test_invalid_response_preserves_existing_history(self):
        h,path,initial=self.history();before=path.read_bytes()
        with self.assertRaises(TypeError): h.record_turn('next',None)
        self.assertEqual(path.read_bytes(),before);self.assertEqual(h.history,initial)
    def test_failed_replace_cleans_only_staged_file(self):
        h,path,initial=self.history();before=path.read_bytes()
        with mock.patch.object(HISTORY_GLOBALS['os'],'replace',side_effect=OSError('synthetic replace failure')):
            with self.assertRaises(OSError):h.record_turn('next','response')
        self.assertEqual(path.read_bytes(),before); self.assertEqual(h.history,initial)
        self.assertEqual(list(path.parent.iterdir()),[path])
    def test_corrupt_archive_is_preserved(self):
        h,path,initial=self.history();path.write_text('{bad json')
        with self.assertRaises(ValueError):h.record_turn('next','response')
        self.assertEqual(path.read_text(),'{bad json');self.assertEqual(h.history,initial)
    def test_existing_update_file_api_still_accepts_prestored_user(self):
        h,path,initial=self.history();h.store_history(h.history+[{'role':'user','content':'legacy'}])
        h.update_file('legacy','response')
        expected=initial+[{'role':'user','content':'legacy'},{'role':'assistant','content':'response'}]
        self.assertEqual(h.history,expected);self.assertEqual(json.loads(path.read_text()),expected)


if __name__ == '__main__':
    print('SOURCE_SHA256='+hashlib.sha256(SOURCE.read_bytes()).hexdigest())
    unittest.main(verbosity=2)
