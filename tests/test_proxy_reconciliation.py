import unittest
from unittest.mock import PropertyMock, patch

from scraper import ExitKind, ExitSpec

from lncrawl.context import ctx
from lncrawl.services.scraper import ScraperService


class ProxyReconciliationTests(unittest.TestCase):
    def test_added_proxy_preserves_existing_leases_and_serves_new_sessions(self):
        service = ScraperService()
        old = [
            ExitSpec(url=f"socks5h://127.0.0.1:{port}", kind=ExitKind.ISP, label=str(port))
            for port in (1001, 1002)
        ]
        new = old + [ExitSpec(url="socks5h://127.0.0.1:1003", kind=ExitKind.ISP, label="1003")]
        with (
            patch.object(service, "_exits", return_value=old),
            patch.object(
                type(ctx.config.crawler),
                "spread_across_exits",
                new_callable=PropertyMock,
                return_value=True,
            ),
        ):
            original = service.states()
            original[0].exits.lease("https://example.com")
            with patch.object(service, "_exits", return_value=new):
                service.reconcile()
            updated = service.states()
            self.assertEqual(len(updated), 3)
            self.assertIs(updated[0], original[0])
            self.assertEqual(updated[0].exits.lease("https://example.com").spec.label, "1001")
            self.assertEqual(updated[2].exits.lease("https://example.net").spec.label, "1003")


if __name__ == "__main__":
    unittest.main()
