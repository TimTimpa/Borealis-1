import time
from machine import Pin, I2C, SPI

import config

from drivers.display_ssd1306 import SSD1306_I2C
from drivers.sensor_sht31 import SHT31
from drivers.rtc_ds3231 import DS3231
from drivers.storage_sdcard import SDCard
from drivers.input_button import Button
from drivers.output_led import LED

from app.timekeeping import Timekeeper
from app.logging import SdLogger
from app.ui import Ui


class App:
    def __init__(self):
        # --- I2C peripherals ---
        self.i2c = I2C(
            config.I2C_ID,
            sda=Pin(config.I2C_SDA),
            scl=Pin(config.I2C_SCL),
            freq=config.I2C_FREQ,
        )

        self.oled = SSD1306_I2C(
            config.OLED_WIDTH,
            config.OLED_HEIGHT,
            self.i2c,
            addr=config.OLED_I2C_ADDR,
        )

        self.sensor = SHT31(self.i2c, addr=config.SHT31_ADDR)
        self.rtc = DS3231(self.i2c, address=config.DS3231_ADDR)
        self.time = Timekeeper(self.rtc)
        self.ui = Ui(self.oled)

        # --- Button ---
        self.button = Button(
            pin_num=config.BUTTON_PIN,
            pull=config.BUTTON_PULL,
            active_level=config.BUTTON_ACTIVE_LEVEL,
            debounce_ms=config.BUTTON_DEBOUNCE_MS,
        )

        # --- LEDs ---
        self.red_led = LED(config.RED_LED_PIN, active_high=config.LED_ACTIVE_HIGH)
        self.green_led = LED(config.GREEN_LED_PIN, active_high=config.LED_ACTIVE_HIGH)

        # --- SD card over SPI ---
        self.spi = SPI(
            config.SD_SPI_ID,
            baudrate=config.SD_BAUDRATE,
            polarity=0,
            phase=0,
            sck=Pin(config.SD_SCK),
            mosi=Pin(config.SD_MOSI),
            miso=Pin(config.SD_MISO),
        )
        self.sd_cs = Pin(config.SD_CS, Pin.OUT)

        self.sd_logger = SdLogger(mount_point=config.SD_MOUNT_POINT)
        self.sd_ok = self._init_sd()

        # --- state ---
        self.experiment_running = False
        self.last_sample_ms = time.ticks_ms()

    def _init_sd(self) -> bool:
        try:
            sd = SDCard(self.spi, self.sd_cs, baudrate=config.SD_BAUDRATE)
            return self.sd_logger.mount(sd)
        except Exception:
            return False

    def _set_off_state(self):
        if self.experiment_running:
            self.sd_logger.stop()
        self.experiment_running = False

        self.red_led.on()
        self.green_led.off()

        utc_iso = self.time.utc_iso()
        self.ui.show_off(utc_iso)

    def _set_on_state(self):
        if not self.experiment_running:
            # start log file (if SD ok)
            utc_iso = self.time.utc_iso()
            self.sd_logger.start_new(utc_iso)
            self.experiment_running = True

        self.green_led.on()
        self.red_led.off()

    def run(self):
        # On boot, show OFF until switch says otherwise
        self._set_off_state()

        while True:
            on = self.button.is_active()

            if not on:
                self._set_off_state()
                time.sleep_ms(50)
                continue

            # ON state
            self._set_on_state()

            now = time.ticks_ms()
            if time.ticks_diff(now, self.last_sample_ms) >= config.SAMPLE_INTERVAL_MS:
                self.last_sample_ms = now

                temp_c, rh = self.sensor.read()
                utc_iso = self.time.utc_iso()

                # Log if SD available and file open
                self.sd_logger.write_row(utc_iso, temp_c, rh)

                # Update display
                self.ui.show_on(temp_c, rh, utc_iso)

            time.sleep_ms(10)
