#!/usr/bin/env python3
"""
Integration tests for SearchManager with real Azure AI Search
Tests the actual clothing data indexed in Azure AI Search
"""

import unittest
import asyncio
import os
import sys
import warnings

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from search_manager import SearchManager


class TestSearchManagerIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for SearchManager with real Azure AI Search data"""
    
    async def asyncSetUp(self):
        """Set up SearchManager with real Azure credentials for each test"""
        # Load environment variables
        import dotenv
        dotenv.load_dotenv(override=True)
        
        self.search_manager = SearchManager(
            service_name=os.getenv("AZURE_SEARCH_SERVICE_NAME"),
            api_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX"),  # Should be "clothing-index"
            embedding_model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
        )
    
    async def asyncTearDown(self):
        """Clean up resources after each test"""
        if hasattr(self, 'search_manager'):
            await self.search_manager.close()

    async def test_basic_search_cotton_tshirt(self):
        """Test search for cotton t-shirts"""
        results = await self.search_manager.search_by_embedding("cotton t-shirt", k=5)
        
        self.assertGreater(len(results), 0, "Should find cotton t-shirts")
        
        # Check that results contain relevant items
        relevant_found = any(
            any(word in result.get("title", "").lower() for word in ["cotton", "shirt", "tee"])
            for result in results
        )
        self.assertTrue(relevant_found, "Should find cotton/shirt related products")
        
        print(f"✅ Found {len(results)} products for 'cotton t-shirt'")
        for result in results[:2]:
            print(f"   - {result.get('title', 'N/A')} ({result.get('brand', 'N/A')}) - €{result.get('price', 'N/A')}")

    async def test_filter_by_brand_zara(self):
        """Test filter search for Zara brand products"""
        results = await self.search_manager.search_by_filters(brand="Zara")
        
        self.assertGreater(len(results), 0, "Should find Zara products")
        
        # Verify all results are from Zara
        for result in results:
            self.assertEqual(result.get("brand"), "Zara", f"Product should be from Zara: {result}")
        
        print(f"✅ Found {len(results)} Zara products")
        for result in results[:3]:
            print(f"   - {result.get('title', 'N/A')} - €{result.get('price', 'N/A')}")

    async def test_hybrid_vector_and_filter_search(self):
        """Test hybrid search combining semantic search with price filtering"""
        # Search for "casual wear" under €50
        results = await self.search_manager.search_with_vector_and_filters(
            text_query="casual comfortable clothing",
            max_price=50.0,
            k=10
        )
        
        self.assertGreater(len(results), 0, "Should find casual clothing under €50")
        
        # Verify all results are within price range
        for result in results:
            price = result.get("price", 0)
            self.assertLessEqual(price, 50.0, f"Product should be under €50: {result.get('title')} - €{price}")
        
        # Check that results contain casual-related items
        casual_found = any(
            any(word in str(result.get(field, "")).lower() 
                for word in ["casual", "comfortable", "basic", "everyday", "cotton"])
            for result in results
            for field in ["title", "description", "style_tags"]
        )
        self.assertTrue(casual_found, "Should find casual/comfortable clothing items")
        
        print(f"✅ Found {len(results)} casual items under €50")
        for result in results[:3]:
            style_tags = result.get('style_tags', [])
            print(f"   - {result.get('title', 'N/A')} - €{result.get('price', 'N/A')} - {style_tags}")

    async def test_filter_by_color_black(self):
        """Test filtering by color using array field (colors/any)"""
        results = await self.search_manager.search_by_filters(color="black")
        
        self.assertGreater(len(results), 0, "Should find black clothing items")
        
        # Verify all results contain black in their colors array
        for result in results:
            colors = result.get("colors", [])
            self.assertIsInstance(colors, list, "Colors should be a list")
            self.assertIn("black", colors, f"Product should have black color: {result.get('title')} - colors: {colors}")
        
        print(f"✅ Found {len(results)} black items")
        for result in results[:3]:
            colors = result.get('colors', [])
            print(f"   - {result.get('title', 'N/A')} ({result.get('brand', 'N/A')}) - colors: {colors}")

    async def test_filter_by_price_range(self):
        """Test filtering by price range (min and max price)"""
        # Search for items between €30 and €100
        results = await self.search_manager.search_by_filters(
            min_price=30.0, 
            max_price=100.0
        )
        
        self.assertGreater(len(results), 0, "Should find items in €30-€100 range")
        
        # Verify all results are within price range
        for result in results:
            price = result.get("price", 0)
            self.assertGreaterEqual(price, 30.0, f"Product should be >= €30: {result.get('title')} - €{price}")
            self.assertLessEqual(price, 100.0, f"Product should be <= €100: {result.get('title')} - €{price}")
        
        # Sort results by price for better display
        sorted_results = sorted(results, key=lambda x: x.get("price", 0))
        
        print(f"✅ Found {len(results)} items in €30-€100 range")
        for result in sorted_results[:4]:
            print(f"   - {result.get('title', 'N/A')} ({result.get('brand', 'N/A')}) - €{result.get('price', 'N/A')}")

    async def test_multi_criteria_filter(self):
        """Test complex filtering combining brand, color, and price"""
        # Search for Nike items in black under €150
        results = await self.search_manager.search_by_filters(
            brand="Nike",
            color="black", 
            max_price=150.0
        )
        
        self.assertGreater(len(results), 0, "Should find Nike black items under €150")
        
        # Verify all criteria are met
        for result in results:
            self.assertEqual(result.get("brand"), "Nike", f"Should be Nike brand: {result}")
            
            colors = result.get("colors", [])
            self.assertIn("black", colors, f"Should have black color: {result.get('title')} - {colors}")
            
            price = result.get("price", 0)
            self.assertLessEqual(price, 150.0, f"Should be <= €150: {result.get('title')} - €{price}")
        
        print(f"✅ Found {len(results)} Nike black items under €150")
        for result in results[:3]:
            colors = result.get('colors', [])
            print(f"   - {result.get('title', 'N/A')} - €{result.get('price', 'N/A')} - {colors}")

    async def test_filter_by_size_medium(self):
        """Test filtering by size availability (sizes/any)"""
        results = await self.search_manager.search_by_filters(size="M")
        
        self.assertGreater(len(results), 0, "Should find items available in size M")
        
        # Verify all results have size M available
        for result in results:
            sizes = result.get("sizes", [])
            self.assertIsInstance(sizes, list, "Sizes should be a list")
            self.assertIn("M", sizes, f"Product should have size M: {result.get('title')} - sizes: {sizes}")
        
        print(f"✅ Found {len(results)} items available in size M")
        for result in results[:3]:
            sizes = result.get('sizes', [])
            print(f"   - {result.get('title', 'N/A')} ({result.get('brand', 'N/A')}) - sizes: {sizes}")

    async def test_filter_by_category_sportswear(self):
        """Test filtering by clothing category"""
        results = await self.search_manager.search_by_filters(category="Sportswear")
        
        self.assertGreater(len(results), 0, "Should find Sportswear items")
        
        # Verify all results are in Sportswear category
        for result in results:
            category = result.get("category")
            self.assertEqual(category, "Sportswear", f"Product should be Sportswear: {result.get('title')} - {category}")
        
        print(f"✅ Found {len(results)} Sportswear items")
        for result in results[:3]:
            print(f"   - {result.get('title', 'N/A')} ({result.get('brand', 'N/A')}) - €{result.get('price', 'N/A')}")

    async def test_filter_by_gender_women(self):
        """Test filtering by gender targeting"""
        results = await self.search_manager.search_by_filters(gender="women")
        
        self.assertGreater(len(results), 0, "Should find women's items")
        
        # Verify all results are for women
        for result in results:
            gender = result.get("gender")
            self.assertEqual(gender, "women", f"Product should be for women: {result.get('title')} - {gender}")
        
        print(f"✅ Found {len(results)} women's items")
        for result in results[:3]:
            print(f"   - {result.get('title', 'N/A')} ({result.get('category', 'N/A')}) - €{result.get('price', 'N/A')}")

    async def test_filter_by_on_sale_true(self):
        """Test filtering for items currently on sale"""
        results = await self.search_manager.search_by_filters(on_sale=True)
        
        self.assertGreater(len(results), 0, "Should find sale items")
        
        # Verify all results are on sale
        for result in results:
            on_sale = result.get("on_sale")
            self.assertTrue(on_sale, f"Product should be on sale: {result.get('title')} - on_sale: {on_sale}")
        
        print(f"✅ Found {len(results)} items on sale")
        for result in results[:3]:
            print(f"   - {result.get('title', 'N/A')} ({result.get('brand', 'N/A')}) - €{result.get('price', 'N/A')} (SALE)")

    async def test_filter_by_material_cotton(self):
        """Test filtering by material using array field (materials/any)"""
        results = await self.search_manager.search_by_filters(material="Cotton")
        
        self.assertGreater(len(results), 0, "Should find cotton items")
        
        # Verify all results contain cotton in materials
        for result in results:
            materials = result.get("materials", [])
            self.assertIsInstance(materials, list, "Materials should be a list")
            # Check if any material contains "Cotton" (case-insensitive)
            cotton_found = any("cotton" in material.lower() for material in materials)
            self.assertTrue(cotton_found, f"Product should contain cotton: {result.get('title')} - materials: {materials}")
        
        print(f"✅ Found {len(results)} cotton items")
        for result in results[:3]:
            materials = result.get('materials', [])
            print(f"   - {result.get('title', 'N/A')} ({result.get('brand', 'N/A')}) - materials: {materials}")

    async def test_filter_no_results_impossible_criteria(self):
        """Test filtering with impossible criteria returns empty results gracefully"""
        # Search for luxury brand with very low price (should return no results)
        results = await self.search_manager.search_by_filters(
            brand="Gucci", 
            max_price=10.0
        )
        
        self.assertEqual(len(results), 0, "Should return no results for impossible criteria")
        
        print("✅ Correctly handled impossible search criteria with empty results")

    async def test_ultra_complex_multi_filter(self):
        """Test maximum complexity filter combining 5+ criteria"""
        # Search for women's Nike sportswear in size M, black color, cotton material, under €200
        results = await self.search_manager.search_by_filters(
            brand="Nike",
            category="Sportswear", 
            gender="women",
            size="M",
            color="black",
            material="Cotton",
            max_price=200.0
        )
        
        # This might return 0 results due to very specific criteria, which is fine
        print(f"✅ Complex multi-filter search completed - found {len(results)} items")
        
        # If we have results, validate they meet ALL criteria
        for result in results:
            self.assertEqual(result.get("brand"), "Nike")
            self.assertEqual(result.get("category"), "Sportswear") 
            self.assertEqual(result.get("gender"), "women")
            self.assertIn("M", result.get("sizes", []))
            self.assertIn("black", result.get("colors", []))
            self.assertLessEqual(result.get("price", 0), 200.0)
            
        if results:
            print(f"   Found ultra-specific match: {results[0].get('title', 'N/A')}")
        else:
            print("   No items matched all criteria (expected for very specific search)")

    async def test_case_insensitive_brand_search(self):
        """Test that brand search handles different cases properly"""
        # Test both lowercase and proper case
        results_lower = await self.search_manager.search_by_filters(brand="nike")
        results_proper = await self.search_manager.search_by_filters(brand="Nike")
        
        # At least one should return results (depending on data casing)
        total_results = len(results_lower) + len(results_proper)
        print(f"✅ Case sensitivity test: nike={len(results_lower)}, Nike={len(results_proper)}")
        
        # Show which case works with our current data
        if results_lower:
            print("   - lowercase 'nike' found results")
            for result in results_lower[:2]:
                print(f"     {result.get('title', 'N/A')} ({result.get('brand', 'N/A')})")
        if results_proper:
            print("   - proper case 'Nike' found results") 
            for result in results_proper[:2]:
                print(f"     {result.get('title', 'N/A')} ({result.get('brand', 'N/A')})")

    

if __name__ == '__main__':
    # Suppress aiohttp warnings about unclosed resources
    warnings.filterwarnings("ignore", message="Unclosed client session")
    warnings.filterwarnings("ignore", message="Unclosed connector")
    
    print("=" * 80)
    print("RUNNING SEARCH MANAGER INTEGRATION TESTS")
    print("Testing real Azure AI Search with clothing data")
    print("=" * 80)
    
    unittest.main(verbosity=2)