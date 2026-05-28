import unittest

from zou.app.utils.fido import DEFAULT_FIDO_RP_ID, get_fido_rp_id


class FidoTestCase(unittest.TestCase):
    def test_get_fido_rp_id_from_empty_domain(self):
        self.assertEqual(get_fido_rp_id(""), DEFAULT_FIDO_RP_ID)

    def test_get_fido_rp_id_from_host_with_port(self):
        self.assertEqual(get_fido_rp_id("example.com:8080"), "example.com")

    def test_get_fido_rp_id_from_url(self):
        self.assertEqual(
            get_fido_rp_id("https://example.com:8443"), "example.com"
        )
