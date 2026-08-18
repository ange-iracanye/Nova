import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LaunchContractTests(unittest.TestCase):
    def test_required_brand_assets_exist(self):
        self.assertTrue((ROOT / "frontend/public/brand/nova-logo.svg").exists())
        self.assertTrue((ROOT / "frontend/src/config/brand.js").exists())
        self.assertTrue((ROOT / "frontend/src/components/NovaLogo.jsx").exists())

    def test_chat_page_exists_and_is_not_replaced_by_landing_page(self):
        chat = ROOT / "frontend/src/pages/Chat.jsx"
        self.assertTrue(chat.exists())
        self.assertGreater(chat.stat().st_size, 10_000)

    def test_launch_document_exists(self):
        self.assertTrue((ROOT / "docs/V1_PUBLIC_LAUNCH.md").exists())
        self.assertTrue((ROOT / "docs/PERFORMANCE_V1.md").exists())

    def test_frontend_has_production_metadata(self):
        index = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
        self.assertIn("nova-logo.svg", index)
        self.assertIn("Nova AI", index)
        self.assertIn("description", index)


if __name__ == "__main__":
    unittest.main()
