# UK Train Monitor

UK Train Monitor is a Home Assistant integration that provides real-time train status and delay information for UK trains. This integration uses the [RTT](https://www.realtimetrains.co.uk/) API to fetch train data.

## Installation

### HACS Installation

1. Ensure that you have [HACS](https://hacs.xyz/) installed in your Home Assistant setup.
2. Go to the HACS section in Home Assistant.
3. Click on "Integrations".
4. Click on the three dots in the top right corner and select "Custom repositories".
5. Add the repository URL: `https://github.com/wyvernp/uk_trains` and select the category as "Integration".
6. Find "UK Train Monitor" in the HACS integrations list and click "Install".

### Manual Installation

1. Clone the repository into your Home Assistant `custom_components` directory:
    ```sh
    git clone https://github.com/wyvernp/uk_trains.git custom_components/uk_trains
    ```

2. Restart Home Assistant to load the new integration.

## Configuration

1. Go to the Home Assistant Configuration page.
2. Click on "Integrations".
3. Click on the "+ Add Integration" button.
4. Search for "UK Train Monitor" and follow the setup instructions.
5. create an account at https://www.realtimetrains.co.uk/ and note down username / password

### Configuration Options

- **Start Station Code**: The station code for the starting station.
- **End Station Code**: The station code for the ending station.
- **Departure Time (HH:MM)**: The departure time in HH:MM format.
- **App ID**: Your RTT API App ID.
- **App Key**: Your RTT API App Key.

## Sensors

This integration provides the following sensors:

### Train Status Sensor

Displays the real-time status of the train.

### Train Delay Sensor

Displays the delay time of the train in minutes.

## Example Configuration

```yaml
sensor:
  - platform: uk_trains
    start_station: "START_CODE"
    end_station: "END_CODE"
    departure_time: "HH:MM"
    app_id: "YOUR_APP_ID"
    app_key: "YOUR_APP_KEY"
