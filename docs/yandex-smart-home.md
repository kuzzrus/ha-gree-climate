# Yandex Smart Home and Yaha Cloud

Yandex Smart Home treats every Home Assistant `climate` entity as a thermostat by default. Home Assistant has no climate device class that marks an entity as an air conditioner. This type must therefore be set in the Yandex Smart Home integration.

Yandex also has a fixed list of mode names. Gree fan modes such as `medium_low` and louver positions such as `fixed_upper` are not on that list. Without a manual mapping, Yandex shows fallback buttons named 1 to 10.

## Find the entity ID

Open **Settings > Developer tools > States** in Home Assistant and find the main Gree climate entity. Copy its entity ID. The example below uses `climate.your_ac`. Replace it with your ID.

## Add the Yandex mapping

Add this block to `configuration.yaml`. If `yandex_smart_home:` already exists, merge `entity_config` into the existing block. Do not add a second `yandex_smart_home:` key.

```yaml
yandex_smart_home:
  entity_config:
    climate.your_ac:
      type: thermostat.ac
      modes:
        fan_speed:
          auto: auto
          min: low
          low: medium_low
          medium: medium
          high: medium_high
          max: high
          quiet: quiet
          turbo: turbo
        swing:
          stationary: default
          auto: full_swing
          max:
            - fixed_upper
            - swing_upper
          high:
            - fixed_upper_middle
            - swing_upper_middle
          medium:
            - fixed_middle
            - swing_middle
          low:
            - fixed_lower_middle
            - swing_lower_middle
          min:
            - fixed_lower
            - swing_lower
```

This configuration keeps every fan speed. For vertical airflow, Yandex shows seven clear choices instead of numbered buttons. A partial swing range and the matching fixed position share one Yandex button because Yandex has no separate names for the Gree ranges. Selecting the button from Yandex sets the fixed position. All twelve vertical modes and all horizontal modes remain available in Home Assistant.

## Apply the change

1. Check the Home Assistant configuration and restart Home Assistant.
2. Delete the old thermostat from the **Дом с Алисой** app.
3. Update the device list for Yaha Cloud.
4. Open the device again. Its type should be **Кондиционер**. Fan speed buttons should have names such as **Минимальный**, **Низкая**, **Средняя**, **Высокая** and **Максимальный**. Airflow buttons should no longer use numbers.

Yandex requires the old device to be deleted after a type change. Updating the list without deleting it can leave the old thermostat type in place.

See the Yaha Cloud documentation for [device types](https://docs.yaha-cloud.ru/master/config/entity/#type) and [mode mappings](https://docs.yaha-cloud.ru/master/config/modes/).
