import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocsWorkflowTests(unittest.TestCase):
    def test_readme_documents_bedrockviewer_and_trader_default(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("BedrockViewer", text)
        self.assertIn("--include-trader-trades", text)
        self.assertIn("disabled by default", text)

    def test_workflow_has_false_trader_default(self):
        text = (ROOT / ".github" / "workflows" / "build-addon.yml").read_text(encoding="utf-8")
        self.assertIn("include_trader_trades", text)
        self.assertIn("default: false", text)
        self.assertIn("--include-trader-trades", text)


if __name__ == "__main__":
    unittest.main()
