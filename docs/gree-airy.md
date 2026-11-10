# Gree Airy

Gree Airy uses a newer Wi-Fi module with Wi-Fi and Bluetooth setup. The indoor
unit model is useful, but the Wi-Fi module firmware decides whether local
control works.

## Before setup

1. Add the unit to the Gree+ app and connect it to a 2.4 GHz Wi-Fi network.
2. Give the unit a fixed DHCP lease. This keeps its IP address stable.
3. Allow UDP port 7000 between Home Assistant and the unit.
4. Use Home Assistant 2026.3 or newer.

The [official Airy product page](https://gree.com.ua/ru/catalog/bytovye-konditsionery/nastennye-split-sistemy-s-invertorom/seryya-airy-inverter-r-32/gwh18avdxe-k6dna1a-gwh18avdxe-k6dna1a.html)
describes the updated Wi-Fi and Bluetooth module.

## Add the unit

1. Install the integration and restart Home Assistant.
2. Go to **Settings** > **Devices & Services** > **Add Integration**.
3. Search for **Кондиционер Gree**.
4. Pick **Local network** first. If the unit is on another VLAN, add its IP
   under **Extra Hosts**.
5. Leave **Encryption Version** on **Auto-Detect**.
6. Enable only the features that the setup flow finds on the unit.

Use the Gree Cloud method when the unit does not allow a local bind. A cloud
login can sign the Gree+ app out because Gree allows one active account session.

## Airy features

The integration can expose these Airy features when the unit reports their
protocol properties:

- cooling, heating, auto, dry and fan-only modes;
- normal fan speeds, plus Turbo and Quiet;
- fixed and moving vertical and horizontal louvers;
- indoor temperature and humidity;
- humidity control and a humidity target;
- Fresh Air for units with a ventilation module;
- X-Fan, Sleep, 8°C Smart Heat and Power Save;
- Health mode, also called cold plasma or ionizer;
- display light, automatic display brightness and command beeps.

Airy advertises seven physical fan speeds. The local protocol reports its normal
speed levels through `WdSpd`. Turbo and Quiet are separate properties, so Home
Assistant shows them as extra fan modes.

Self-cleaning and UVC control are not exposed. The known local protocol does not
provide reliable properties for them.

## I Feel temperature test

On one Airy with Wi-Fi firmware `U-4MWB65VRV2.10.bin`, enabling I Feel on the
physical remote changed both `EnvTem` and `TemSen` to the remote temperature
plus 40. Heating the remote changed both raw values from 66 to 73, which means
26 to 33 °C. `TemSor` and `BlkTemCom` stayed at zero.

The `gree_custom.test_ifeel_temperature` action can test whether the unit also
accepts these values over its current connection. This is experimental. See
[Actions and diagnostics](actions.md#gree_customtest_ifeel_temperature).

On the tested Airy, a Wi-Fi write was accepted immediately but the unit restored
its own sensor values within about one minute. The optional **External
temperature transmission** switch on the external thermostat therefore repeats
the selected room sensor value every 20 seconds. Each refresh includes the two
beeper properties in their silent state. Transmission also works while the
external thermostat entity is off. The switch is shown when the unit reports at
least one of `EnvTem` and `TemSen`.

## Firmware limits

Local control is known to work on some Airy units with Wi-Fi firmware V2.10.
There are reports of V2.07 units that answer on UDP port 7000 but do not complete
the encrypted bind. See
[upstream issue 468](https://github.com/RobHofmann/HomeAssistant-GreeClimateComponent/issues/468).

Some V2.10 modules return an incomplete response when device information is
requested in one batch. The integration detects this response and retries the
information fields one at a time. This fallback is used only during binding.

If local setup fails:

1. Try cloud setup in the integration.
2. Download the integration diagnostics.
3. Record the `hid` and `ver` fields of the Wi-Fi module.
4. Attach the diagnostics and Home Assistant logs to a bug report.

The general checks are in [troubleshooting.md](troubleshooting.md).
