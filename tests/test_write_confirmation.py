"""Actual WebSocket send/response methods, fake transport and real asyncio futures.

No sockets, credentials or charger are used by the transport double.
"""
import ast
import asyncio
import hashlib
import hmac
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE=Path(__file__).resolve().parents[1]/'custom_components/goecharger_api2/pygoecharger_ha/__init__.py'


def bridge(sender,secured=False):
    tree=ast.parse(SOURCE.read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GoeChargerApiV2Bridge')
    cls.bases=[]
    cls.body=[n for n in cls.body if getattr(n,'name','') in
        ('_ws_send_command','extract_ws_message_data','_fail_pending_acknowledgements')]
    ns={'asyncio':asyncio,'json':json,'hmac':hmac,'hashlib':hashlib,
        '_LOGGER':logging.getLogger(__name__),'API_KEYS_TO_IGNORE_FROM_WS':[]}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),'actual-bridge','exec'),ns)
    obj=ns['GoeChargerApiV2Bridge']()
    store={}
    obj._ws_request_storage=SimpleNamespace(set=lambda k,v:store.update({k:v}),get=lambda k:store.get(k))
    obj._ws_pending_ack={};obj._ws_states={};obj._ws_request_id_counter=0
    obj._ws_secured=secured;obj._ws_hashed_password=b'synthetic-key'
    obj._ws_connection=SimpleNamespace(send_json=lambda msg:sender(obj,msg))
    return obj


@pytest.mark.parametrize('secured',[False,True])
@pytest.mark.parametrize('success,expected',[(True,True),(False,False),('true',False)])
def test_only_matching_inner_boolean_response_confirms(secured,success,expected):
    async def scenario():
        async def send(obj,msg):
            inner=json.loads(msg['data']) if secured else msg
            obj.extract_ws_message_data({'type':'response','requestId':999,'success':True})
            assert not obj._ws_pending_ack[str(inner['requestId'])].done()
            if secured:
                obj.extract_ws_message_data({'type':'response','requestId':msg['requestId'],'success':True})
                assert not obj._ws_pending_ack[str(inner['requestId'])].done()
            obj.extract_ws_message_data({'type':'response','requestId':inner['requestId'],'success':success})
        obj=bridge(send,secured)
        assert await obj._ws_send_command('tcl',10,wait_for_response=True) is expected
        assert not obj._ws_pending_ack
    asyncio.run(scenario())


def test_sending_without_ack_does_not_confirm(monkeypatch):
    async def timeout(future,timeout):
        raise asyncio.TimeoutError
    monkeypatch.setattr(asyncio,'wait_for',timeout)
    async def scenario():
        async def send(obj,msg):pass
        obj=bridge(send)
        assert not await obj._ws_send_command('ids',{},wait_for_response=True)
        assert not obj._ws_pending_ack
    asyncio.run(scenario())


def test_legacy_send_only_path_remains_available():
    async def scenario():
        async def send(obj,msg):pass
        obj=bridge(send)
        assert await obj._ws_send_command('amp',10)
        assert not obj._ws_pending_ack
    asyncio.run(scenario())


def test_disconnect_fails_pending_wait_without_hanging():
    async def scenario():
        async def send(obj,msg):obj._fail_pending_acknowledgements()
        obj=bridge(send)
        assert not await obj._ws_send_command('tcl',10,wait_for_response=True)
    asyncio.run(scenario())


def test_concurrent_requests_are_not_cross_confirmed():
    async def scenario():
        messages=[]
        async def send(obj,msg):
            messages.append(msg)
            if len(messages)==2:
                obj.extract_ws_message_data({'type':'response','requestId':messages[1]['requestId'],'success':True})
                obj.extract_ws_message_data({'type':'response','requestId':messages[0]['requestId'],'success':False})
        obj=bridge(send)
        result=await asyncio.gather(obj._ws_send_command('tcl',10,wait_for_response=True),
            obj._ws_send_command('ids',{},wait_for_response=True))
        assert result==[False,True] and not obj._ws_pending_ack
    asyncio.run(scenario())


def test_send_exception_cleans_pending_future():
    async def scenario():
        async def send(obj,msg):raise OSError('synthetic disconnect')
        obj=bridge(send)
        with pytest.raises(OSError):await obj._ws_send_command('tcl',10,wait_for_response=True)
        assert not obj._ws_pending_ack
    asyncio.run(scenario())


def test_cancelled_caller_cleans_future_and_late_reply_is_ignored():
    async def scenario():
        async def send(obj,msg):pass
        obj=bridge(send)
        task=asyncio.create_task(obj._ws_send_command('tcl',10,wait_for_response=True))
        await asyncio.sleep(0)
        assert '1' in obj._ws_pending_ack
        task.cancel()
        with pytest.raises(asyncio.CancelledError):await task
        assert not obj._ws_pending_ack
        obj.extract_ws_message_data({'type':'response','requestId':1,'success':True})
    asyncio.run(scenario())
