"""
Flask API for printing flashcards on a thermal receipt printer.

Renders each flashcard as an HTML/CSS image (see html_to_image.py) sized to
the printer's paper width, then sends it to an ESC/POS thermal printer.
"""

from flask import Flask, request, jsonify
from escpos.printer import Usb
from html_to_image import create_flashcard_image_sync

app = Flask(__name__)

# USB vendor/product ID and profile are specific to the connected printer model.
# Swap escpos.printer.Usb for Network or Serial if printing over a different connection.
p = Usb(0x0483, 0x5743, profile="TM-T20II")
PRINTER_WIDTH_PX = 576  # must match the printer's paper width in pixels

@app.route('/print-flashcards', methods=['POST'])
def print_flashcards():
    """
    Endpoint to receive flashcard data and print them as square format receipts.
    Expects JSON array of objects with 'question' and 'answer' fields.
    """
    try:
        flashcards = request.get_json()

        # Validate input
        if not flashcards or not isinstance(flashcards, list):
            return jsonify({'error': 'Invalid input. Expected array of flashcard objects.'}), 400
        
        # Process each flashcard
        printed_count = 0
        for card in flashcards:
            if not isinstance(card, dict) or 'question' not in card or 'answer' not in card:
                continue  # Skip invalid cards
            
            # Print the flashcard
            print_flashcard(card['question'], card['answer'])
            printed_count += 1
        
        return jsonify({
            'success': True, 
            'message': f'Successfully printed {printed_count} flashcards'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Printing failed: {str(e)}'}), 500

def print_flashcard(question, answer):
    """
    Print a single flashcard as an image in square format.
    Generates HTML/CSS based flashcard and converts to image for printing.
    """
    try:
        # Generate flashcard image from HTML template
        flashcard_image = create_flashcard_image_sync(question, answer)
        
        # Set center alignment before printing image
        p.set(align='center')
        
        # Print the image with center alignment
        # The image() method automatically handles sizing for thermal printers
        p.image(flashcard_image)
        
        # Add some spacing after the image
        p.text("\n")
        
        # Cut paper (if printer supports it)
        p.cut()
        
    except Exception as e:
        # Image rendering (Playwright/Pillow) can fail independently of the printer
        # connection, so fall back to a plain-text layout rather than dropping the card.
        print(f"Image generation failed: {e}. Falling back to text printing.")
        print_flashcard_text_fallback(question, answer)

def print_flashcard_text_fallback(question, answer):
    """
    Fallback text-based printing method, used when image generation fails.
    """
    # Center align for the entire card
    p.set(align='center')
    
    # Print header separator
    p.text("=" * 32 + "\n")
    p.text("FLASHCARD\n")
    p.text("=" * 32 + "\n\n")
    
    # Print question
    p.set(font='b')  # Bold text
    p.text("QUESTION:\n")
    p.set(normal_textsize=True)
    p.text(f"{question}\n\n")
    
    # Print separator
    p.text("-" * 32 + "\n\n")
    
    # Print answer
    p.set(font='b')  # Bold text
    p.text("ANSWER:\n")
    p.set(normal_textsize=True)
    p.text(f"{answer}\n\n")
    
    # Print footer separator
    p.text("=" * 32 + "\n\n")
    
    # Cut paper (if printer supports it)
    p.cut()

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'flashcard-printer'}), 200

if __name__ == '__main__':
    # Run the Flask app in debug mode
    app.run(debug=True, host='0.0.0.0', port=5000)