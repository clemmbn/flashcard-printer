"""
HTML to Image conversion utility for flashcard printing.
Uses Playwright to render HTML templates as images.
"""

import asyncio
import os
from PIL import Image
from io import BytesIO
from playwright.async_api import async_playwright

class HTMLToImageConverter:
    def __init__(self, template_dir="templates"):
        """
        Initialize the HTML to Image converter.
        
        Args:
            template_dir (str): Directory containing HTML templates
        """
        self.template_dir = template_dir
        self.browser = None
        self.context = None
    
    async def start_browser(self):
        """Start the headless browser for image generation."""
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                viewport={'width': 576, 'height': 576},  # Taller viewport to accommodate variable height
                device_scale_factor=1
            )
    
    async def close_browser(self):
        """Close the browser and cleanup resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        self.browser = None
        self.context = None
    
    def render_template(self, template_name, **kwargs):
        """
        Render HTML template with provided data.
        
        Args:
            template_name (str): Name of the HTML template file
            **kwargs: Template variables to substitute
            
        Returns:
            str: Rendered HTML content
        """
        template_path = os.path.join(self.template_dir, template_name)
        
        # Read template file
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Simple template substitution (you could use Jinja2 for more complex templates)
        for key, value in kwargs.items():
            placeholder = f"{{{{ {key} }}}}"
            template_content = template_content.replace(placeholder, str(value))
        
        return template_content
    
    async def html_to_image(self, html_content, css_path=None):
        """
        Convert HTML content to PIL Image.
        
        Args:
            html_content (str): HTML content to convert
            css_path (str): Optional path to external CSS file
            
        Returns:
            PIL.Image: Generated image
        """
        await self.start_browser()
        
        # Create a new page
        page = await self.context.new_page()
        
        try:
            # Set page content
            await page.set_content(html_content)
            
            # If external CSS is provided, add it
            if css_path and os.path.exists(css_path):
                await page.add_style_tag(path=css_path)
            
            # Wait for any fonts or resources to load
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot of the entire page
            screenshot_bytes = await page.screenshot(
                full_page=True,
                type='png'
            )
            
            # Convert to PIL Image
            image = Image.open(BytesIO(screenshot_bytes))
            
            # Ensure the image width is exactly 576px, but allow variable height
            if image.size[0] != 576:
                # Calculate new height maintaining aspect ratio
                aspect_ratio = image.size[1] / image.size[0]
                new_height = int(576 * aspect_ratio)
                image = image.resize((576, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        finally:
            await page.close()
    
    async def create_flashcard_image(self, question, answer):
        """
        Create a flashcard image from question and answer text.
        
        Args:
            question (str): Question text
            answer (str): Answer text
            
        Returns:
            PIL.Image: Generated flashcard image
        """
        # Render the HTML template
        html_content = self.render_template(
            'flashcard.html',
            question=question,
            answer=answer
        )
        
        # Convert to image
        css_path = os.path.join(self.template_dir, 'styles.css')
        image = await self.html_to_image(html_content, css_path)
        
        return image

# Convenience function for synchronous usage
def create_flashcard_image_sync(question, answer, template_dir="templates"):
    """
    Synchronous wrapper for creating flashcard images.
    
    Args:
        question (str): Question text
        answer (str): Answer text
        template_dir (str): Directory containing templates
        
    Returns:
        PIL.Image: Generated flashcard image
    """
    async def _create():
        converter = HTMLToImageConverter(template_dir)
        try:
            image = await converter.create_flashcard_image(question, answer)
            return image
        finally:
            await converter.close_browser()
    
    # Run the async function
    return asyncio.run(_create())

# Example usage
if __name__ == "__main__":
    # Test the converter
    question = "What is the capital of France?"
    answer = "Paris is the capital and most populous city of France."
    
    image = create_flashcard_image_sync(question, answer)
    image.save("test_flashcard.png")
    print("Test flashcard saved as test_flashcard.png")
