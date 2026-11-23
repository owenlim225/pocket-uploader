import unittest
from unittest.mock import patch

import uploader as u


def clips(*names):
    return [("/Movies/" + name, 100, 1, str(i)) for i, name in enumerate(names)]


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.db = u.database(":memory:")
        self.addCleanup(self.db.close)

    def titles(self, items):
        return [row["title"] for row, _ in u.inventory(self.db, "phone", items)]

    def test_order_and_fallback(self):
        items = clips("20261031_171400.mp4", "20261031_165259.mp4",
                      "Beach day.mp4", "20260230_010101.mp4")
        rows = u.inventory(self.db, "phone", items)
        self.assertEqual([(r["title"], uri) for r, uri in rows],
                         [("October 31, 2026 PART 1", "1"), ("October 31, 2026 PART 2", "0"),
                          ("20260230_010101", "3"), ("Beach day", "2")])

    def test_later_earlier_clip(self):
        self.assertEqual(self.titles(clips("20261107_222117.mp4")), ["November 7, 2026"])
        self.assertEqual(self.titles(clips("20261107_222117.mp4", "20261107_010101.mp4")),
                         ["November 7, 2026 PART 2", "November 7, 2026"])

    def test_recovery_and_identity(self):
        items = clips("A/day.mp4", "B/day.mp4")
        rows = u.inventory(self.db, "phone", items)
        entry = rows[0][0]["rowid"]
        u.change(self.db, entry, "pending", "review")
        self.assertEqual([r["state"] for r, _ in u.inventory(self.db, "phone", items)],
                         ["review", "pending"])
        u.change(self.db, entry, "review", "done")
        with self.assertRaises(u.Pause):
            u.change(self.db, entry, "review", "pending")

    @patch("uploader.adb")
    def test_completion_requires_title_and_success(self, adb):
        adb.return_value = ("  Notification List:\n    NotificationRecord(x pkg=com.google.android.youtube "
                            "user=0)\nandroid.title=String (Beach)\nandroid.text=String (Upload complete)\n")
        self.assertTrue(u.confirmations("device", "Beach"))
        self.assertFalse(u.confirmations("device", "Other"))
        adb.return_value = adb.return_value.replace("Upload complete", "Uploading")
        self.assertFalse(u.confirmations("device", "Beach"))

