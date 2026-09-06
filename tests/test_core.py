import unittest
from subtitle_shift_cli.__main__ import parse, render, transform
class Tests(unittest.TestCase):
 def test_shift(self):
  items=parse("1\n00:00:01,000 --> 00:00:02,500\nHello\n"); moved=transform(items,1.5); self.assertEqual(moved[0]["start"],2.5); self.assertIn("00:00:04,000",render(moved))
if __name__=="__main__": unittest.main()
