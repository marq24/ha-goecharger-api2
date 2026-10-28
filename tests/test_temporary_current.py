"""Run actual validation, number methods and service routing with fake devices.

No Home Assistant installation, network or charger is started. AST extraction
keeps the tested production bodies unchanged; the HA base classes are doubles.
"""
import ast
import importlib.util
import logging
import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/goecharger_api2"
spec = importlib.util.spec_from_file_location("temporary_current", ROOT / "temporary_current.py")
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


def run(coroutine):
    """AsyncMock awaits finish inline; reject unexpected real asynchronous I/O."""
    try:
        coroutine.send(None)
    except StopIteration as done:
        return done.value
    finally:
        coroutine.close()
    raise AssertionError("Unexpected asynchronous I/O")


def data(**changes):
    return {"tcl": None, "var": 22, "ama": 32, "mca": 6, **changes}


@pytest.mark.parametrize("variant,limit,ama,expected", [(11,False,32,16),(22,False,32,32),(22,True,32,16),(22,False,10,10)])
def test_hardware_and_user_ceiling(variant, limit, ama, expected):
    assert validation.current_bounds(data(var=variant,ama=ama),limit) == (6,expected)


@pytest.mark.parametrize("value", [None,True,False,"6",float("nan"),float("inf"),-1,0,5,6.5,33,
    pytest.param(10**1000,id="oversized-integer")])
def test_reject_invalid_current(value):
    with pytest.raises(ValueError):
        validation.validate_current(value,data())


@pytest.mark.parametrize("changes", [{"var":None},{"var":True},{"var":99},{"ama":None},{"mca":float("inf")},{"ama":5},{"mca":17,"var":11}])
def test_missing_or_inconsistent_capability(changes):
    with pytest.raises(ValueError):
        validation.validate_current(6,data(**changes))


def test_missing_support_and_inactive_support_are_distinct():
    with pytest.raises(ValueError):
        validation.validate_current(6,{"var":11,"ama":16,"mca":6})
    assert validation.validate_current(6,data(tcl=None)) == 6
    with pytest.raises(ValueError):
        validation.current_bounds(None)


@pytest.mark.parametrize("reply", [None,{}, {"err":"rejected"},{"tcl":True},{"tcl":False},{"tcl":8}])
def test_no_false_acknowledgement(reply):
    with pytest.raises(ValueError):
        validation.require_acknowledgement(reply,9)


class Base:
    available = True
    native_min_value = 6
    native_max_value = 32


class ServiceValidationError(ValueError):
    pass


def production_class(filename, name, base=Base):
    tree=ast.parse((ROOT/filename).read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)
    cls.bases=[ast.Name(id="Base",ctx=ast.Load())]
    cls.body=[n for n in cls.body if getattr(n,"name","") not in ("__init__","async_added_to_hass")]
    namespace={"Base":base,"ServiceCall":object,"Tag":SimpleNamespace(TCL=SimpleNamespace(key="tcl")),
        "ServiceValidationError":ServiceValidationError,"math":math,"_LOGGER":logging.getLogger(__name__),
        "validate_current":validation.validate_current,"require_acknowledgement":validation.require_acknowledgement,
        "current_bounds":validation.current_bounds,"is_finite_number":validation.is_finite_number}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),filename,"exec"),namespace)
    return namespace[name],namespace


def test_native_entity_renews_same_value_and_preserves_other_settings():
    cls,_=production_class("number.py","GoeChargerNumber")
    obj=cls();obj.data_key="tcl"
    obj.coordinator=SimpleNamespace(data=data(tcl=9,amp=12),limit_to16a=False,async_write_key=AsyncMock(return_value={"tcl":9}))
    assert obj.available and obj.native_value==9 and obj.native_max_value==32
    for _ in range(2):
        run(obj.async_set_native_value(9))
    assert obj.coordinator.async_write_key.await_count==2
    assert all(c.args==("tcl",9,obj) for c in obj.coordinator.async_write_key.call_args_list)
    assert obj.coordinator.data["amp"]==12 and obj.coordinator.data["ama"]==32


def test_unsupported_entity_unavailable_and_inactive_value_unknown():
    cls,_=production_class("number.py","GoeChargerNumber")
    obj=cls();obj.data_key="tcl";obj.coordinator=SimpleNamespace(data=data(),limit_to16a=False)
    assert obj.available and obj.native_value is None
    del obj.coordinator.data["tcl"]
    assert not obj.available


@pytest.mark.parametrize("target", ["first","second"])
def test_actual_service_routes_only_selected_charger(target):
    cls,ns=production_class("service.py","GoeChargerApiV2Service")
    coordinators={e:SimpleNamespace(data=data(),limit_to16a=False,async_write_key=AsyncMock(return_value={"tcl":9})) for e in ("first","second")}
    ns["_COORDINATOR_PER_CONFIG_ENTRY_ID_MAP"]=coordinators
    obj=cls();obj._hass=SimpleNamespace(config_entries=SimpleNamespace(async_get_entry=lambda e:SimpleNamespace(disabled_by=None) if e in coordinators else None))
    result=run(obj.set_temporary_current_limit(SimpleNamespace(data={"configid":target,"current":9},return_response=True)))
    assert result=={"success":True,"current":9,"acknowledged":True}
    assert coordinators[target].async_write_key.await_count==1
    assert sum(c.async_write_key.await_count for c in coordinators.values())==1


@pytest.mark.parametrize("target", [None,"missing","disabled"])
def test_service_never_falls_back_from_invalid_target(target):
    cls,ns=production_class("service.py","GoeChargerApiV2Service")
    writer=AsyncMock()
    ns["_COORDINATOR_PER_CONFIG_ENTRY_ID_MAP"]={"valid":SimpleNamespace(async_write_key=writer)}
    obj=cls();obj._hass=SimpleNamespace(config_entries=SimpleNamespace(async_get_entry=lambda e:SimpleNamespace(disabled_by="user") if e=="disabled" else None))
    with pytest.raises(ServiceValidationError):
        run(obj.set_temporary_current_limit(SimpleNamespace(data={"configid":target,"current":9},return_response=True)))
    writer.assert_not_awaited()


def test_polling_includes_expiry_even_in_hibernation():
    ns={};exec((ROOT/"pygoecharger_ha/const.py").read_text(),ns)
    assert "tcl" in ns["FILTER_MIN_STATES"].split(",")
    assert "tcl" in ns["FILTER_ALL_STATES"].split(",")
    assert "tcl" not in ns["FILTER_ALL_CONFIG"].split(",")


@pytest.mark.parametrize("unavailable", [None,[],"unavailable"])
def test_missing_coordinator_data_is_clean_validation_error(unavailable):
    with pytest.raises(ValueError):
        validation.validate_current(6,unavailable)


@pytest.mark.parametrize("field", ["ama","mca","tcl"])
def test_oversized_reported_integer_is_rejected_cleanly(field):
    with pytest.raises(ValueError):
        validation.validate_current(6,data(**{field:10**1000}))


@pytest.mark.parametrize("value", [True,"unavailable",float("nan"),float("inf"),-1,6.5])
def test_invalid_reported_limit_is_unavailable(value):
    cls,_=production_class("number.py","GoeChargerNumber")
    obj=cls();obj.data_key="tcl";obj.coordinator=SimpleNamespace(data=data(tcl=value),limit_to16a=False)
    assert not obj.available


def test_native_value_handles_missing_data_and_oversized_report():
    cls,_=production_class("number.py","GoeChargerNumber")
    obj=cls();obj.data_key="tcl";obj.coordinator=SimpleNamespace(data=None,limit_to16a=False)
    assert obj.native_value is None and not obj.available
    obj.coordinator.data=data(tcl=10**1000)
    assert obj.native_value is None and not obj.available


@pytest.mark.parametrize("reply,accepted", [({"tcl":True},True),({"tcl":False},False),
    ({"tcl":"unknown key"},False),({"tcl":"out of range"},False),({"tcl":1},False),({},False)])
def test_actual_http_bridge_requires_boolean_acceptance(reply,accepted):
    tree=ast.parse((ROOT/"pygoecharger_ha/__init__.py").read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="GoeChargerApiV2Bridge")
    method=next(n for n in cls.body if getattr(n,"name",None)=="_write_values_int")
    ns={"Tag":SimpleNamespace(TCL=SimpleNamespace(key="tcl"),IDS=SimpleNamespace(key="ids")),
        "_LOGGER":logging.getLogger(__name__)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),"bridge","exec"),ns)
    class Response:
        status=200
        json=AsyncMock(return_value=reply)
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
    obj=SimpleNamespace(_logkey="synthetic",host_url="example.invalid",token=None,_timeout=None,
        web_session=SimpleNamespace(get=lambda *a,**kw:Response()))
    result=run(ns['_write_values_int'](obj,{"tcl":"9"},"tcl",9))
    assert (result=={"tcl":9}) is accepted
