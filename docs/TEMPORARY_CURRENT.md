# Temporary current limit

This adds an optional, disabled-by-default `number` entity and the
`goecharger_api2.set_temporary_current_limit` action. Select the charger
explicitly and provide whole amperes within its known hardware/user bounds:

```yaml
action: goecharger_api2.set_temporary_current_limit
data:
  configid: YOUR_CHARGER_CONFIG_ENTRY
  current: 10
response_variable: limit_result
```

The existing bridge's successful write response is required; a rejected write
raises an error. `acknowledged` means the API accepted the command, not that a
vehicle is drawing this current. Check independent power/current measurements
when verifying physical behaviour. The requested `amp` and absolute `ama`
settings are untouched. Repeating the same command renews the limit.

The manufacturer's `tcl` setting expires after approximately ten minutes
without renewal. This integration does not create a renewal timer, clear it on
unload or assume that zero/null has a documented reset meaning. Supported
commands are whole amperes from the known minimum (at least 6 A) to the known
hardware/user ceiling. A missing `tcl` is unsupported; a reported null has no
numeric value and is displayed as unknown. Its meaning is not guessed from
the response alone. Invalid reported values and unknown ratings reject writes.

Polling includes this value in active and hibernation status requests so its
expiry is not hidden by the 24-hour configuration cache. WebSocket status
continues to use the existing coordinator. Firmware compatibility beyond
reported capability requires device testing; unsupported devices stay
unavailable. This is not a charging Stop or an independent watchdog: expiry
can permit more current. Keep an independent response to loss of control.

Validation (no charger/network):

```sh
python -m pip install pytest
python -m pytest tests -q
```

Original integration authorship and Apache-2.0 licence are retained. Prepared
with AI assistance; hardware expiry, firmware variants and actual charging
still require a controlled pilot before replacing an existing controller.

### Transport confirmation

A requested confirmation waits up to three seconds for the matching inner
WebSocket response. A successful socket send or secured-envelope response is
not an acknowledgement. Timeout, disconnect and rejected responses fail the
wait. Legacy send-only calls retain their existing behaviour. HTTP success
requires a literal JSON `true`; truthy error strings are not acceptance.
This small transport correction is shared with the other reliability
contribution and must not be applied twice. No hardware response/latency or
firmware expiry has been tested by these synthetic checks.
