import unittest
from typing import Dict, Any
import json
from openApiToolKit import create_api_toolkit, ask_question

class WeatherAPIToolkitTests(unittest.TestCase):
    """Test suite for the Weather API toolkit implementation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the toolkit and agent for testing."""
        cls.toolkit, cls.agent = create_api_toolkit()
    
    def test_valid_city_request(self):
        """Test weather request for a valid city."""
        cities = ["Roma", "Milano", "Napoli"]
        for city in cities:
            with self.subTest(city=city):
                result = ask_question(self.agent, city)
                self.assertIsNotNone(result)
                self.verify_weather_response(result)
    
    def test_invalid_city_request(self):
        """Test weather request for invalid cities."""
        invalid_cities = ["", "123", "NonExistentCity"]
        for city in invalid_cities:
            with self.subTest(city=city):
                with self.assertRaises(Exception):
                    ask_question(self.agent, city)
    
    def verify_weather_response(self, response: Dict[str, Any]):
        """Verify the structure and content of the weather response."""
        if isinstance(response, str):
            # Try to parse JSON response if it's a string
            response = json.loads(response)
            
        self.assertIn('temperatura', response)
        self.assertIn('condizioni', response)
        self.assertIsInstance(response['temperatura'], (int, float))
        self.assertIsInstance(response['condizioni'], str)
        
        # Verify temperature is within reasonable range
        self.assertGreater(response['temperatura'], -50)
        self.assertLess(response['temperatura'], 50)
        
        # Verify conditions is a non-empty string
        self.assertGreater(len(response['condizioni']), 0)

def run_tests():
    """Run the test suite."""
    unittest.main(argv=[''], exit=False)

if __name__ == '__main__':
    run_tests()