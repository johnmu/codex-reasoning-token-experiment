"""Offline checks that differing native context cannot reach the model."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiment/src'))
from identical import payload, PROTOCOL_HEADERS, verify_sent
import identical_addon


class IdenticalTests(unittest.TestCase):
    def test_payload_is_stateless_and_contains_only_shared_inputs(self):
        body=payload('the prompt','shared instructions','gpt-6-luna','medium')
        self.assertEqual(body['tools'], [])
        self.assertEqual(body['instructions'], 'shared instructions')
        self.assertEqual(body['input'][0]['content'][0]['text'], 'the prompt')
        self.assertFalse({'client_metadata','previous_response_id','prompt_cache_key','generate'} & body.keys())

    def test_byte_gate_rejects_even_whitespace_differences(self):
        raw=b'{"model":"gpt-6-luna"}\n'
        events=[{'direction':'out','text':raw.decode()}, {'kind':'controlled_headers','headers':PROTOCOL_HEADERS}]
        self.assertTrue(verify_sent(events,raw,PROTOCOL_HEADERS)['identical_request_verified'])
        events[0]['text']='{ "model": "gpt-6-luna" }\n'
        self.assertFalse(verify_sent(events,raw,PROTOCOL_HEADERS)['identical_request_verified'])

    def test_native_tools_and_metadata_are_replaced_not_merged(self):
        frozen=json.dumps(payload('prompt','instructions','gpt-6-luna','medium')).encode()
        original={'type':'response.create','input':[{'tools':['auth-specific-tool']}],
                  'client_metadata':{'session_id':'different'},'previous_response_id':'different'}
        message=SimpleNamespace(content=json.dumps(original).encode(),from_client=True,injected=False)
        flow=SimpleNamespace(id='test',request=SimpleNamespace(host='api.openai.com',path='/v1/responses'),
                             websocket=SimpleNamespace(messages=[message]))
        with patch.object(identical_addon,'BODY',frozen), patch.object(identical_addon,'SENT',False), \
             patch.object(identical_addon.observe,'record'), patch.object(identical_addon.observe,'message') as saved:
            identical_addon.websocket_message(flow)
            self.assertEqual(message.content,frozen)
            self.assertEqual(saved.call_args.args[2].encode(),frozen)

    def test_warmup_is_dropped_and_acknowledged_locally(self):
        message=SimpleNamespace(content=b'{"type":"response.create","generate":false}',
                                from_client=True,injected=False,drop=lambda:None)
        flow=SimpleNamespace(id='test',request=SimpleNamespace(host='chatgpt.com',path='/backend-api/codex/responses'),
                             websocket=SimpleNamespace(messages=[message]))
        with patch.object(identical_addon.observe,'record'), patch.object(identical_addon,'SENT',False), \
             patch.object(identical_addon,'prefix_acknowledgement') as ack:
            identical_addon.websocket_message(flow)
            ack.assert_called_once_with(flow)
            self.assertFalse(identical_addon.SENT)

    def test_acknowledgement_injection_is_to_client_not_upstream(self):
        call=Mock()
        ctx=SimpleNamespace(master=SimpleNamespace(commands=SimpleNamespace(call=call)))
        frozen=json.dumps(payload('prompt','instructions','gpt-6-luna','medium')).encode()
        with patch.dict(sys.modules,{'mitmproxy':SimpleNamespace(ctx=ctx)}), patch.object(identical_addon,'BODY',frozen):
            identical_addon.prefix_acknowledgement('flow')
        self.assertEqual(call.call_count,2)
        self.assertTrue(all(args.args[2] is True for args in call.call_args_list))

    def test_only_required_auth_and_transport_headers_survive(self):
        headers={'authorization':'secret','cookie':'private','chatgpt-account-id':'account',
                 'upgrade':'websocket','sec-websocket-key':'nonce','x-session-id':'variable',
                 'x-codex-routing-hint':'variable','user-agent':'variable'}
        flow=SimpleNamespace(id='test',request=SimpleNamespace(host='chatgpt.com',path='/backend-api/codex/responses',
                             method='GET',raw_content=b'',headers=headers))
        with patch.object(identical_addon,'HEADERS',PROTOCOL_HEADERS), patch.object(identical_addon.observe,'record'):
            identical_addon.request(flow)
        self.assertEqual(headers['authorization'],'secret')
        self.assertEqual(headers['cookie'],'private')
        self.assertNotIn('x-session-id',headers)
        self.assertNotIn('x-codex-routing-hint',headers)
        for name,value in PROTOCOL_HEADERS.items():
            self.assertEqual(headers[name],value)

    def test_changed_payload_cannot_make_addon_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            (p/'payload.json').write_text('{}')
            (p/'headers.json').write_text('{}')
            settings={'EXPERIMENT_IDENTICAL_PAYLOAD':str(p/'payload.json'),'EXPERIMENT_IDENTICAL_SHA256':'wrong',
                      'EXPERIMENT_IDENTICAL_HEADERS':str(p/'headers.json'),
                      'EXPERIMENT_HEADERS_SHA256':hashlib.sha256(b'{}').hexdigest(),
                      'EXPERIMENT_CAPTURE_READY_FILE':str(p/'ready')}
            with patch.dict(os.environ,settings), self.assertRaises(AssertionError):
                identical_addon.load(None)
            self.assertFalse((p/'ready').exists())


if __name__ == '__main__':
    unittest.main()
