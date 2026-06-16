# Flashcard Printer

A small Flask API that turns question/answer flashcards into printed receipts on a
thermal (ESC/POS) printer. Each flashcard is rendered as styled HTML, converted to
an image with a headless browser, and sent to the printer — so you get proper
typography and layout instead of plain ASCII text.

## How it works

1. `app.py` exposes a Flask endpoint that accepts flashcards as JSON.
2. `html_to_image.py` renders `templates/flashcard.html` (styled by
   `templates/styles.css`) with Playwright and screenshots it as a PNG sized to the
   printer's paper width.
3. The image is sent to the printer via [python-escpos](https://python-escpos.readthedocs.io/).
4. If image rendering fails for any reason, the card falls back to a plain-text
   printout so nothing is silently dropped.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A USB ESC/POS-compatible thermal printer (tested with an Epson TM-T20II)

## Setup

```bash
uv sync
uv run playwright install chromium
```

Edit the printer connection in [app.py](app.py) to match your hardware:

```python
p = Usb(0x0483, 0x5743, profile="TM-T20II")
```

Find your printer's vendor/product ID with `lsusb` (Linux) or `system_profiler
SPUSBDataType` (macOS). Swap `Usb` for `escpos.printer.Network` or `Serial` if
you're not connecting over USB.

## Running

```bash
uv run python app.py
```

The server starts on `http://0.0.0.0:5000`.

## API

### `POST /print-flashcards`

Prints one or more flashcards. Body is a JSON array of `{question, answer}` objects:

```bash
curl -X POST http://localhost:5000/print-flashcards \
  -H "Content-Type: application/json" \
  -d '[{"question": "What is the capital of France?", "answer": "Paris"}]'
```

Response:

```json
{"success": true, "message": "Successfully printed 1 flashcards"}
```

### `GET /health`

Basic health check, returns `{"status": "healthy", "service": "flashcard-printer"}`.

## Customizing the flashcard look

Edit `templates/flashcard.html` and `templates/styles.css`. The renderer screenshots
the page at a fixed width of 576px (matching standard 80mm thermal paper) and a
variable height, so layouts should grow vertically rather than relying on a fixed
viewport.

## To go further

I have created an n8n automation that takes a pdf, creates flashcards out of it and prints them using this script. A lot can be done with this.
