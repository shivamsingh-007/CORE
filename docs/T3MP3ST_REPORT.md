# T3MP3ST Bug Report
Generated: 2026-07-03T17:09:51.254475
Project: .

## MEDIUM (8)
- [scanner] `app\agents\t3mp3st\dynamic_engine.py:150` **Unhandled exception from write_text()**
  `write_text()` can raise — wrap in try/except

- [scanner] `app\agents\t3mp3st\review_engine.py:53` **Unhandled exception from read_text()**
  `read_text()` can raise — wrap in try/except

- [scanner] `app\agents\t3mp3st\review_engine.py:64` **Unhandled exception from read_text()**
  `read_text()` can raise — wrap in try/except

- [scanner] `app\agents\t3mp3st\scan_engine.py:50` **Unhandled exception from read_bytes()**
  `read_bytes()` can raise — wrap in try/except

- [scanner] `tests\test_integration.py:22` **Unhandled exception from write_text()**
  `write_text()` can raise — wrap in try/except

- [scanner] `tests\test_integration.py:23` **Unhandled exception from write_text()**
  `write_text()` can raise — wrap in try/except

- [scanner] `tests\test_integration.py:24` **Unhandled exception from write_text()**
  `write_text()` can raise — wrap in try/except

- [scanner] `tests\test_integration.py:77` **Unhandled exception from read_text()**
  `read_text()` can raise — wrap in try/except

## INFO (1)
- [dynamic] `app/session/manager.py:0` **Session manager handles corruption gracefully**
  Confirmed: corrupt JSON returns empty SessionState, not crash
  Fix: None needed
