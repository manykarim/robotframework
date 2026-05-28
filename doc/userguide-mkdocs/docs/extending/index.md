# Extending Robot Framework

Robot Framework's real power comes from its library interface. [Creating test libraries](creating-test-libraries.md) explains how to write Python libraries using the static, hybrid, or dynamic API — if your keyword belongs in Python code rather than a `.robot` file, this is the place to start. For reacting to execution events in real time or running libraries as separate processes, the [listener interface](listener-interface.md) and [remote library interface](remote-library.md) have you covered.

- [Creating test libraries](creating-test-libraries.md) — Writing Python libraries using the static, hybrid, or dynamic API.
- [Listener interface](listener-interface.md) — Reacting to execution events in real time via listener classes.
- [Remote library interface](remote-library.md) — Running test libraries as separate processes or on remote machines.
- [Dynamic library API](dynamic-library-api.md) — Implementing libraries whose keywords are determined dynamically at runtime.
- [Parser interface](parser-interface.md) — Writing custom parsers to support non-standard test data formats.
