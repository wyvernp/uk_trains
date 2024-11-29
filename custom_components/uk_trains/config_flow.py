"""Config flow for UK Trains integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UK Trains."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            is_valid = await self._test_credentials(user_input)
            if is_valid:
                await self.async_set_unique_id(
                    f"{user_input['start_station']}_{user_input['end_station']}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{user_input['start_station']} to {user_input['end_station']}",
                    data=user_input,
                )
            else:
                errors["base"] = "invalid_credentials"

        data_schema = vol.Schema(
            {
                vol.Required("start_station"): str,
                vol.Required("end_station"): str,
                vol.Optional("time"): str,  # Time in HH:MM format
                vol.Required("username"): str,
                vol.Required("password"): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def _test_credentials(self, user_input):
        """Test if the provided credentials are valid."""
        start = user_input["start_station"]
        end = user_input["end_station"]
        time = user_input.get("time")
        username = user_input["username"]
        password = user_input["password"]

        # Use the RTT API to validate credentials and journey
        import aiohttp
        from datetime import datetime

        session = aiohttp_client.async_get_clientsession(self.hass)
        try:
            url = f"https://api.rtt.io/api/v1/json/search/{start}/to/{end}"
            if time:
                now = datetime.now()
                date_str = now.strftime("%Y%m%d")  # Changed to match API requirements
                time_str = time.replace(":", "")
                url += f"/{date_str}/{time_str}"

            credentials = f"{username}:{password}"
            import base64

            b64_credentials = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
            headers = {"Authorization": f"Basic {b64_credentials}"}

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "services" in data and data["services"]:
                        return True
                elif response.status == 401:
                    _LOGGER.error("Invalid credentials provided.")
                    return False
                else:
                    _LOGGER.error(f"Unexpected response status: {response.status}")
            return False
        except Exception as e:
            _LOGGER.error(f"Error testing credentials: {e}")
            return False
