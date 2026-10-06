"""Offline checks for redaction, unchanged forwarding, and token/latency capture."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import capture_addon
from capture import summarize_wire


class CaptureTests(unittest.TestCase):
    def test_headers_are_redacted_without_changing_live_headers(self):
        headers = {'Authorization': 'secret', 'Cookie': 'private', 'User-Agent': 'codex-test'}
        saved = capture_addon.safe_headers(headers)
        self.assertEqual(saved, {'authorization': '[redacted]', 'cookie': '[redacted]', 'user-agent': 'codex-test'})
        self.assertEqual(headers['Authorization'], 'secret')

    def test_websocket_message_is_observed_without_being_changed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'wire.jsonl'
            body = b'{"type":"response.create","model":"gpt-6-luna"}'
            message = SimpleNamespace(content=body, from_client=True)
            flow = SimpleNamespace(id='test', request=SimpleNamespace(host='api.openai.com', path='/v1/responses'),
                                   websocket=SimpleNamespace(messages=[message]))
            with patch.dict(os.environ, {'EXPERIMENT_CAPTURE_FILE': str(path)}):
                capture_addon.websocket_message(flow)
            self.assertIs(message.content, body)
            self.assertEqual(json.loads(path.read_text())['text'], body.decode())

    def test_fragmented_sse_is_observed_and_forwarded_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'wire.jsonl'
            flow = SimpleNamespace(id='test', request=SimpleNamespace(host='api.openai.com', path='/v1/responses'),
                                   response=SimpleNamespace(status_code=200, headers={'content-type':'text/event-stream'}))
            chunks = [b'data: {"type":"response.', b'output_text.delta","delta":"hello"}\n\n', b'']
            with patch.dict(os.environ, {'EXPERIMENT_CAPTURE_FILE': str(path)}):
                capture_addon.responseheaders(flow)
                for chunk in chunks:
                    self.assertIs(flow.response.stream(chunk), chunk)
            events = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(events[-1]['body']['delta'], 'hello')

    def test_wire_summary_ignores_prefix_and_keeps_explicit_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'wire.jsonl'
            usage={'input_tokens':10,'output_tokens':5,'total_tokens':15,'output_tokens_details':{'reasoning_tokens':0},
                   'input_tokens_details':{'cached_tokens':0,'cache_write_tokens':0}}
            request={'type':'response.create','model':'gpt-6-luna','reasoning':{'effort':'medium'}}
            response={'model':'gpt-6-luna','reasoning':{'effort':'medium'},'usage':usage}
            events=[{'time':1,'direction':'out','transport':'websocket','body':{**request,'generate':False}},
                    {'time':2,'direction':'in','body':{'type':'response.completed','response':response}},
                    {'time':3,'direction':'out','transport':'websocket','host':'api.openai.com','path':'/v1/responses','body':request},
                    {'time':4,'direction':'in','body':{'type':'response.output_text.delta','delta':'hello'}},
                    {'time':4.5,'direction':'in','body':{'type':'response.output_text.done','text':'hello'}},
                    {'time':5,'direction':'in','body':{'type':'response.completed','response':response}}]
            path.write_text(''.join(json.dumps(e)+'\n' for e in events))
            native={'inputTokens':10,'outputTokens':5,'totalTokens':15,'reasoningOutputTokens':0,
                    'cachedInputTokens':0,'cacheWriteInputTokens':0}
            result=summarize_wire(path,native)
            self.assertEqual(result['wire_flags'], [])
            self.assertEqual(result['wire_seconds'], 2)
            self.assertEqual(result['wire_first_text_seconds'], 1)
            self.assertEqual(result['server_answer'], 'hello')
            self.assertEqual(result['server_usage']['output_tokens_details']['reasoning_tokens'], 0)
            native['reasoningOutputTokens']=None
            self.assertIn('server_native_token_mismatch', summarize_wire(path,native)['wire_flags'])
            del usage['output_tokens_details']['reasoning_tokens']
            path.write_text(''.join(json.dumps(e)+'\n' for e in events))
            self.assertIn('missing_server_tokens', summarize_wire(path,native)['wire_flags'])


if __name__ == '__main__':
    unittest.main()
