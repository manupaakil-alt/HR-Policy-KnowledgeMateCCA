import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import agent


class HRRelevanceTests(unittest.TestCase):
    def test_classifier_receives_explicit_hr_scope(self):
        classifier = Mock()
        classifier.invoke.return_value = SimpleNamespace(is_hr_related=True)
        question = "Can my boss deny time off for a medical appointment?"

        with patch.object(agent, "hr_relevance_classifier", classifier):
            self.assertTrue(agent._is_hr_question(question))

        messages = classifier.invoke.call_args.args[0]
        self.assertEqual(messages[0][0], "system")
        self.assertIn("When the wording is ambiguous", messages[0][1])
        self.assertIn(
            "Do not decide based on whether the policy database", messages[0][1]
        )
        self.assertIn("well-known HR managers in the US", messages[0][1])
        self.assertEqual(messages[1], ("user", question))

    def test_classifier_respects_structured_decision(self):
        classifier = Mock()
        classifier.invoke.return_value = SimpleNamespace(is_hr_related=False)

        with patch.object(agent, "hr_relevance_classifier", classifier):
            self.assertFalse(agent._is_hr_question("How do I bake sourdough?"))


if __name__ == "__main__":
    unittest.main()
