# Integration tests

Regression tests for bugs fixed in the integration. They run without a charger, without network
access and without credentials: the test framework blocks real sockets, and the bridge is faked.

```sh
python3.14 -m venv .venv && . .venv/bin/activate
python -m pip install -r requirements_dev.txt
python -m pytest tests/integration -q
```

Python 3.14 is required by the current `pytest-homeassistant-custom-component`, which also pins the
Home Assistant release it was built for. `msgpack` is listed in the manifest, but the test
framework does not install manifest requirements, so it is part of `requirements_dev.txt`.
