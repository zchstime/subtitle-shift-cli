from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from subtitle_shift_cli.__main__ import main, parse, render_vtt


class WebVTTTests(unittest.TestCase):
    def test_shift_and_convert_both_directions(self):
        with TemporaryDirectory() as directory:
            vtt = Path(directory) / "input.vtt"
            srt = vtt.with_suffix(".srt")
            result = Path(directory) / "output.vtt"
            vtt.write_bytes("WEBVTT\r\n\r\n00:59.500 --> 01:01.100\r\n¡Hola!\r\nDos líneas\r\n".encode("utf-8-sig"))
            main([str(vtt), "--shift", "0.5", "-o", str(srt)])
            self.assertEqual(srt.read_text(encoding="utf-8"),
                             "1\n00:01:00,000 --> 00:01:01,600\n¡Hola!\nDos líneas\n")
            main([str(srt), "-o", str(result)])
            self.assertEqual(result.read_text(encoding="utf-8"),
                             "WEBVTT\n\n00:01:00.000 --> 00:01:01.600\n¡Hola!\nDos líneas\n")

    def test_identifier_and_settings_round_trip(self):
        source = "WEBVTT\n\nspeaker\n01:00:00.010 --> 01:00:01.999 align:start\nOK\n"
        self.assertEqual(render_vtt(parse(source)), source)

    def test_empty_document(self):
        self.assertEqual(render_vtt(parse("WEBVTT\n\n")), "WEBVTT\n\n")

    def test_unsupported_metadata_does_not_overwrite_output(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "input.vtt"
            path.write_text("WEBVTT\n\nNOTE keep me\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                main([str(path), "-o", str(path)])
            self.assertIn("NOTE keep me", path.read_text(encoding="utf-8"))
