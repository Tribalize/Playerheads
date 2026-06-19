import unittest

from playerheads.bedrockviewer import BedrockViewerClient, Profile


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, content=b"", headers=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.content = content
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        return self.responses.pop(0)


class BedrockViewerClientTests(unittest.TestCase):
    def test_resolves_profile_json(self):
        session = FakeSession([
            FakeResponse(json_data={"Gamertag": "PPTribalize", "XUID": "2535407405283318", "skin": True})
        ])
        client = BedrockViewerClient(session=session)

        profile = client.fetch_profile("PPTribalize")

        self.assertEqual(profile, Profile(gamertag="PPTribalize", xuid="2535407405283318", has_skin=True))
        self.assertEqual(session.calls[0][0], "https://bedrockviewer.com/profile/PPTribalize/json")

    def test_download_skin_url_uses_xuid(self):
        self.assertEqual(
            BedrockViewerClient.skin_download_url("2535407405283318"),
            "https://bedrockviewer.com/download-skin/2535407405283318",
        )

    def test_download_skin_requires_png_response(self):
        session = FakeSession([
            FakeResponse(content=b"not html", headers={"Content-Type": "image/png"})
        ])
        client = BedrockViewerClient(session=session)

        content = client.download_skin("2535407405283318")

        self.assertEqual(content, b"not html")

    def test_missing_xuid_raises_value_error(self):
        session = FakeSession([FakeResponse(json_data={"Gamertag": "NoSkin"})])
        client = BedrockViewerClient(session=session)

        with self.assertRaises(ValueError):
            client.fetch_profile("NoSkin")


if __name__ == "__main__":
    unittest.main()
