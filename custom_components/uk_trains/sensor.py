"""Sensor platform for UK Trains."""
import logging
import base64
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers import aiohttp_client
from .const import DOMAIN, ATTRIBUTION

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensor platform."""
    coordinator = TrainDataUpdateCoordinator(hass, entry.data)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            TrainStatusSensor(coordinator, entry.data),
            TrainDelaySensor(coordinator, entry.data),
        ]
    )


class TrainDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the RTT API."""

    def __init__(self, hass, config):
        """Initialize."""
        self.hass = hass
        self.config = config
        super().__init__(
            hass,
            _LOGGER,
            name="Train data coordinator",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from the RTT API within the specified time window."""
        start_station = self.config["start_station"]
        end_station = self.config["end_station"]
        time_str = self.config.get("time")  # Time as HH:MM
        username = self.config["username"]
        password = self.config["password"]

        now = datetime.now()

        # If no time is specified, always fetch data
        if not time_str:
            within_window = True
            train_time = None
        else:
            # Parse the train time into a datetime object
            try:
                train_time = datetime.strptime(time_str, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
            except ValueError:
                _LOGGER.error(f"Invalid time format: {time_str}")
                return self.data  # Return the last known data or None

            # Handle train times that have already passed (crossing midnight)
            if train_time < now - timedelta(hours=1):
                train_time += timedelta(days=1)

            # Calculate time window
            window_start = train_time - timedelta(hours=1)
            window_end = train_time + timedelta(hours=1)

            # Check if current time is within the window
            within_window = window_start <= now <= window_end

        if within_window:
            _LOGGER.debug("Within time window. Fetching data.")
            session = aiohttp_client.async_get_clientsession(self.hass)
            try:
                url = f"https://api.rtt.io/api/v1/json/search/{start_station}/to/{end_station}"

                # Use the train time to construct the URL
                if time_str:
                    date_str = train_time.strftime("%Y/%m/%d")
                    time_str_formatted = time_str.replace(":", "")
                    url += f"/{date_str}/{time_str_formatted}"

                credentials = f"{username}:{password}"
                b64_credentials = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
                headers = {"Authorization": f"Basic {b64_credentials}"}

                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        _LOGGER.error(f"Error fetching data: {response.status}")
                        _LOGGER.debug(f"Response: {await response.text()}")
                        raise UpdateFailed(f"Error fetching data: {response.status}")
                    data = await response.json()
                    return data
            except Exception as e:
                _LOGGER.error(f"Exception during data fetch: {e}")
                raise UpdateFailed(f"Error fetching data: {e}") from e
        else:
            _LOGGER.debug("Outside time window. Skipping data fetch.")
            return self.data  # Return the last known data or None


class TrainStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor to show the train status."""

    def __init__(self, coordinator, config):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config = config
        time = config.get("time", "anytime").replace(":", "")
        time_display = config.get("time", "anytime")
        self._attr_name = (
            f"Train Status {config['start_station']} to {config['end_station']} at {time_display}"
        )
        self._attr_unique_id = (
            f"train_status_{config['start_station']}_{config['end_station']}_{time}"
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return "No data"
        services = self.coordinator.data.get("services", [])
        if services:
            service = services[0]
            loc_detail = service.get("locationDetail", {})
            realtime_departure = loc_detail.get("realtimeDeparture", "Unknown")
            return realtime_departure
        return "No data"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class TrainDelaySensor(CoordinatorEntity, SensorEntity):
    """Sensor to show the train delay time."""

    def __init__(self, coordinator, config):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config = config
        time = config.get("time", "anytime").replace(":", "")
        time_display = config.get("time", "anytime")
        self._attr_name = (
            f"Train Delay {config['start_station']} to {config['end_station']} at {time_display}"
        )
        self._attr_unique_id = (
            f"train_delay_{config['start_station']}_{config['end_station']}_{time}"
        )
        self._attr_device_class = "duration"
        self._attr_native_unit_of_measurement = "minutes"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        services = self.coordinator.data.get("services", [])
        if services:
            service = services[0]
            loc_detail = service.get("locationDetail", {})
            scheduled_dep = loc_detail.get("gbttBookedDeparture")
            realtime_dep = loc_detail.get("realtimeDeparture")

            if scheduled_dep and realtime_dep:
                fmt = "%H%M"
                if realtime_dep in ["Delayed", "Cancelled"]:
                    # Handle special cases
                    return None
                elif realtime_dep == "On time":
                    return 0
                try:
                    scheduled = datetime.strptime(scheduled_dep, fmt)
                    actual = datetime.strptime(realtime_dep, fmt)
                    delay = (actual - scheduled).total_seconds() / 60
                    return int(delay)
                except ValueError:
                    _LOGGER.debug("Unable to parse time strings.")
                    return None
            else:
                return None
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
