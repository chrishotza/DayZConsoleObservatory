"""Accessible historical position data: no proprietary map or live location claims."""
from html.parser import HTMLParser
from pathlib import Path
import json
import shutil
import subprocess
import unittest

from dayz_observatory.server import WEB


class _Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class PositionAccessibilityTests(unittest.TestCase):
    def test_canvas_has_keyboard_readable_text_equivalent(self):
        html = (WEB / "index.html").read_text(encoding="utf-8")
        parser = _Elements()
        parser.feed(html)
        elements = parser.elements
        self.assertTrue(any(tag == "a" and attrs.get("href") == "#workspace"
                            and attrs.get("class") == "skip-link" for tag, attrs in elements))
        self.assertTrue(any(tag == "details" and attrs.get("class") == "position-details"
                            for tag, attrs in elements))
        self.assertTrue(any(tag == "canvas" and attrs.get("aria-describedby") == "positionDisclaimers"
                            for tag, attrs in elements))
        self.assertTrue(any(tag == "table" and attrs.get("class") == "position-table"
                            for tag, attrs in elements))
        self.assertTrue(any(tag == "tbody" and attrs.get("id") == "positionRows"
                            for tag, attrs in elements))
        self.assertEqual(sum(1 for tag, attrs in elements
                             if tag == "th" and attrs.get("scope") == "col"), 4)

    def test_position_text_uses_safe_dom_and_mobile_navigation_is_available(self):
        script = (WEB / "app.js").read_text(encoding="utf-8")
        css = (WEB / "style.css").read_text(encoding="utf-8")
        self.assertIn("function paintPositionTable(pts)", script)
        self.assertIn("paintPositionTable(pts);", script)
        self.assertIn("cell.textContent=value", script)
        self.assertNotIn("innerHTML", script)
        self.assertIn(".site-header nav{display:flex;order:3", css)
        self.assertIn(".skip-link:focus", css)

    def test_position_text_renders_values_and_empty_state_when_node_available(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node unavailable; accessible HTML and safe DOM checks still run")
        js = (WEB / "app.js").read_text(encoding="utf-8")
        function = ("function paintPositionTable(pts){" +
                    js.split("function paintPositionTable(pts){", 1)[1]
                      .split("function paintMap(){", 1)[0])
        harness = r"""
const state={selectedId:'ID1'};
class Element {
  constructor(){this.children=[];this.textContent='';this.className='';this.colSpan=1;}
  append(...children){this.children.push(...children);}
  replaceChildren(){this.children=[];}
}
const nodes={positionRows:new Element(),positionTableSummary:new Element()};
const document={
  getElementById:id=>nodes[id],
  createElement:()=>new Element()
};
const $=id=>document.getElementById(id);
"""
        final = r"""
paintPositionTable([{player_name:'<script>escaped</script>',player_id:'ID1',
  x:17,z:42,occurred_at:'2026-10-16T12:00:00'}]);
const filled={
  count:nodes.positionRows.children.length,
  cells:nodes.positionRows.children[0].children.map(x=>x.textContent),
  selected:nodes.positionRows.children[0].className,
  summary:nodes.positionTableSummary.textContent
};
paintPositionTable([]);
console.log(JSON.stringify({filled,empty:nodes.positionRows.children[0].children[0].textContent}));
"""
        result = subprocess.run([node, "-e", harness + function + final],
                                text=True, capture_output=True, timeout=10, check=True)
        data = json.loads(result.stdout)
        self.assertEqual(data["filled"]["count"], 1)
        self.assertEqual(data["filled"]["cells"],
                         ["<script>escaped</script>", "17", "42", "2026-10-16 12:00:00"])
        self.assertEqual(data["filled"]["selected"], "selected-row")
        self.assertIn("(1)", data["filled"]["summary"])
        self.assertIn("No recorded positions", data["empty"])


if __name__ == "__main__":
    unittest.main()
