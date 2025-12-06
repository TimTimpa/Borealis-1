from machine import Pin, I2C, SPI
from ssd1306 import SSD1306_I2C
from sht31 import SHT31
from ds3231 import DS3231
from sdcard import SDCard
import uos as os
import time

WIDTH = 128
HEIGHT = 64

# ---------- I2C: OLED + SHT31 + DS3231 ----------
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)

oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)
sensor = SHT31(i2c)
rtc_ext = DS3231(i2c)


def get_utc_iso():
    # DS3231.datetime() -> (year, month, day, weekday, hour, minute, second, subsecond)
    y, m, d, wd, hh, mm, ss, sub = rtc_ext.datetime()
    return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}Z"


# ---------- SPI1: SD card ----------
# Pins from your diagram:
#   SCK  = GP10
#   MOSI = GP11
#   MISO = GP12
# We'll use GP13 for CS.
spi = SPI(
    1,
    baudrate=1_000_000,
    polarity=0,
    phase=0,
    sck=Pin(10),
    mosi=Pin(11),
    miso=Pin(12),
)
cs = Pin(13, Pin.OUT)

sd = SDCard(spi, cs)
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")


# ---------- Create experiment log file ----------
start_utc = get_utc_iso()  # e.g. "2025-12-06T14:15:30Z"

# Make a filename-safe version: remove '-' and ':' (not allowed in FAT),
# keep date + time info.
fn_safe = start_utc.replace("-", "").replace(":", "")
# e.g. "20251206T141530Z"

log_path = "/sd/" + fn_safe + ".csv"   # e.g. "/sd/20251206T141530Z.csv"

# Create file and write header
with open(log_path, "w") as f:
    f.write("utc_iso,temp_c,humidity_percent\n")

# Open once for appending during experiment
log_file = open(log_path, "a")


while True:
    # --- Read sensors ---
    temp, hum = sensor.read()
    utc_str = get_utc_iso()

    # --- Log to SD card ---
    # CSV: utc_iso,temp_c,humidity_percent
    log_file.write("{},{:.2f},{:.2f}\n".format(utc_str, temp, hum))
    log_file.flush()  # ensure data is written regularly

    # --- Prepare strings for OLED ---
    date_str = utc_str[0:10]        # "YYYY-MM-DD"
    time_str = utc_str[11:19] + "Z" # "HH:MM:SSZ"

    # --- Update display ---
    oled.fill(0)
    oled.center("Borealis-1", 0)
    oled.text("T: {:.1f} C".format(temp), 0, 16)
    oled.text("H: {:.1f} %".format(hum), 0, 26)
    oled.text(date_str, 0, 38)      # UTC date
    oled.text(time_str, 0, 48)      # UTC time
    oled.show()

    time.sleep(1)
