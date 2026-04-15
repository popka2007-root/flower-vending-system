from __future__ import annotations

import unittest

from flower_vending.simulators.scenarios.customer_flows import run_pickup_timeout_placeholder_scenario


class PickupTimeoutIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_pickup_timeout_is_explicit_placeholder(self) -> None:
        result = await run_pickup_timeout_placeholder_scenario()
        self.assertTrue(result.success)
        self.assertEqual(result.machine_state, "WAITING_FOR_CUSTOMER_PICKUP")
        self.assertTrue(any("placeholder" in note for note in result.notes))


if __name__ == "__main__":
    unittest.main()
