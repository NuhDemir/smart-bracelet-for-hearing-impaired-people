import datetime
import json
import os
import sys
import time
import struct
import serial

# Font boyutları
FONT_SIZE_32 = 0x01
FONT_SIZE_48 = 0x02
FONT_SIZE_64 = 0x03

# Bellek modları
MEM_FLASH = 0x00
MEM_SD = 0x01

# Ekran dönüş açıları
ROTATION_0 = 0x00
ROTATION_90 = 0x01
ROTATION_180 = 0x02
ROTATION_270 = 0x03

class Screen(object):
    """Ekran sınıfı, Waveshare 4.3 inch E-Paper Modülü ile iletişim kurar."""

    def __init__(self, serial_port):
        self.ser = serial.Serial(serial_port, 115200)
        self._buffer = bytearray()
        self._ch_font_size = FONT_SIZE_32
        self._en_font_size = FONT_SIZE_32
        self._memory = MEM_FLASH
        self._rotation = ROTATION_0

    def connect(self):
        """Cihaza bağlan."""
        self.ser.write(b'\x00')

    def handshake(self):
        """Bağlantıyı doğrula."""
        if self.ser.read(1) != b'\x00':
            raise IOError('Bağlantı hatası.')

    def disconnect(self):
        """Cihazdan bağlantıyı kes."""
        self.ser.write(b'\xFF')

    def set_memory(self, memory):
        """Bellek modunu ayarla."""
        self.ser.write(struct.pack('>B', 0xE0 | memory))
        self._memory = memory

    def set_rotation(self, rotation):
        """Ekran dönüş açısını ayarla."""
        self.ser.write(struct.pack('>B', 0xD0 | rotation))
        self._rotation = rotation

    def clear(self):
        """Ekranı temizle."""
        self.ser.write(b'\x10')

    def update(self):
        """Ekranı güncelle."""
        self.ser.write(b'\x20')

    def bitmap(self, x, y, bmp_name):
        """Bitmap görüntüyü ekrana yaz."""
        bmp = self._load_bmp(bmp_name)
        self._buffer += b'\x30' + struct.pack('>HH', x, y) + bmp

    def text(self, x, y, text):
        """Metni ekrana yaz."""
        self._buffer += b'\x40' + struct.pack('>HH', x, y) + text.encode('gb2312')

    def wrap_text(self, x, y, width, text):
        """Metni belirtilen genişlikteki alana sararak ekrana yaz."""
        lines = []
        line = ''
        for word in text.split():
            if self.get_text_width(line + ' ' + word, self._ch_font_size) <= width:
                line += ' ' + word
            else:
                lines.append(line)
                line = word
        lines.append(line)
        for i, line in enumerate(lines):
            self.text(x, y + i * (self._ch_font_size * 2), line)

    def line(self, x0, y0, x1, y1):
        """Çizgi çiz."""
        self._buffer += b'\x50' + struct.pack('>HHHH', x0, y0, x1, y1)

    def set_ch_font_size(self, size):
        """Çince font boyutunu ayarla."""
        self._ch_font_size = size
        self._buffer += b'\x60' + struct.pack('>B', size)

    def set_en_font_size(self, size):
        """İngilizce font boyutunu ayarla."""
        self._en_font_size = size
        self._buffer += b'\x61' + struct.pack('>B', size)

    def get_text_width(self, text, size):
        """Metin genişliğini hesapla."""
        return len(text) * size

    def _load_bmp(self, bmp_name):
        """Bitmap görüntüyü yükle."""
        with open(bmp_name, 'rb') as bmp_file:
            return bmp_file.read()

# Ekran boyutları
screen_width = 800
screen_height = 600
screen = Screen('/dev/ttyAMA0')
screen.connect()
screen.handshake()

# Ekranı temizle ve belleği ayarla
screen.clear()
screen.set_memory(MEM_FLASH)
screen.set_rotation(ROTATION_180)

clock_x = 40
clock_y = 40
temp_x = 0
time_now = datetime.datetime.now()
time_string = time_now.strftime('%H:%M')
date_string = time_now.strftime('%Y-%m-%d')
week_string = [u'Pazartesi', u'Salı', u'Çarşamba', u'Perşembe', u'Cuma', u'Cumartesi', u'Pazar'][time_now.isoweekday() - 1]
if time_string[0] == '0':
    time_string = time_string[1:]
    temp_x += 40

# Saatin bitmap görüntülerini yükle
for c in time_string:
    bmp_name = 'NUM{}.BMP'.format('S' if c == ':' else c)
    screen.bitmap(clock_x + temp_x, clock_y, bmp_name)
    temp_x += 70 if c == ':' else 100

# Tarih ve gün bilgilerini ekle
screen.set_ch_font_size(FONT_SIZE_48)
screen.set_en_font_size(FONT_SIZE_48)
screen.text(clock_x + 350 + 140, clock_y + 10, date_string)
screen.text(clock_x + 350 + 170, clock_y + 70, week_string)

# Çizgi çiz
screen.line(0, clock_y + 160, 800, clock_y + 160)
screen.line(0, clock_y + 161, 800, clock_y + 161)

# Hava durumu verilerini yükle
def weather_fail(msg):
    screen.text(10, clock_y + 170, msg)
    screen.update()
    screen.disconnect()
    sys.exit(1)

weather_data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weather.json')
wdata = {}
try:
    with open(weather_data_file, 'r') as in_file:
        wdata = json.load(in_file)
except IOError:
    weather_fail(u'HATA: Hava durumu verileri yüklenemedi!')

if wdata.get('error'):
    weather_fail(wdata.get('error'))

if int(time.time()) - wdata['update'] > 2 * 3600:
    weather_fail(u'HATA: Hava durumu verileri güncelliğini yitirdi!')

cw = wdata['current_weather']
bmp_name = {u'Güneşli': 'WQING.BMP', u'Bulutlu': 'WYIN.BMP', u'Parçalı Bulutlu': 'WDYZQ.BMP',
            u'Gök Gürültülü Sağanak Yağışlı': 'WLZYU.BMP', u'Yağmurlu': 'WXYU.BMP', u'Kar Yağışlı': 'WXUE.BMP'}.get(cw, None)
if not bmp_name:
    if u'Yağmur' in cw:
        bmp_name = 'WYU.BMP'
    elif u'Kar' in cw:
        bmp_name = 'WXUE.BMP'
    elif u'Dolu' in cw:
        bmp_name = 'WBBAO.BMP'
    elif u'Sis' in cw or u'Duman' in cw:
        bmp_name = 'WWU.BMP'

if bmp_name:
    screen.bitmap(20, clock_y + 240, bmp_name)

# Hava durumu bilgilerini ekle
screen.set_ch_font_size(FONT_SIZE_64)
screen.set_en_font_size(FONT_SIZE_64)

margin_top = 20
weather_y = clock_y + 170
weather_line_spacing = 10
weather_line1_height = 64
weather_line2_height = 42
weather_line3_height = 64
weather_line4_height = 64
weather_text_x = 256 - 30
weather_line5_x = weather_text_x + 64
if len(wdata['current_aq_desc']) > 2:
    weather_line5_x -= 80

screen.text(weather_text_x + 64, weather_y + margin_top, wdata['today_weather'])

tmp0 = u'{current_temp}℃ {current_humidity} %'.format(**wdata)
tmp0 = tmp0.replace('1', '1 ')
screen.text(weather_text_x + 64, weather_y + margin_top +
            weather_line1_height +
            weather_line_spacing +
            weather_line2_height +
            weather_line_spacing, tmp0)

try:
    home_data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'home_air.json')
    hdata = json.load(file(home_data_file, 'r'))
    if int(time.time()) - hdata['update'] < 120:
        tmp0 = u'{temp}℃ {humidity} %'.format(**hdata)
        tmp0 = tmp0.replace('1', '1 ')
        screen.text(weather_text_x + 64, weather_y + margin_top +
                    weather_line1_height +
                    weather_line_spacing +
                    weather_line2_height +
                    weather_line_spacing +
                    weather_line3_height +
                    weather_line_spacing, tmp0)
except Exception as e:
    pass

screen.text(weather_line5_x, weather_y + margin_top +
            weather_line1_height +
            weather_line_spacing +
            weather_line2_height +
            weather_line_spacing +
            weather_line3_height +
            weather_line_spacing +
            weather_line4_height +
            weather_line_spacing,
            u'{current_aq} {current_aq_desc}'.format(**wdata))

screen.set_ch_font_size(FONT_SIZE_32)
screen.set_en_font_size(FONT_SIZE_32)

screen.text(weather_text_x + 64 - 20 - screen.get_text_width(wdata['city_name'], FONT_SIZE_32),
            weather_y + margin_top + 10, wdata['city_name'])

screen.text(weather_text_x - 20, weather_y + margin_top +
            weather_line1_height +
            weather_line_spacing +
            weather_line2_height +
            weather_line_spacing + 10, u'Dış Mekan')

screen.text(weather_text_x - 20, weather_y + margin_top +
            weather_line1_height +
            weather_line_spacing +
            weather_line2_height +
            weather_line_spacing +
            weather_line3_height +
            weather_line_spacing + 10, u'İç Mekan')

screen.text(weather_line5_x - 64 * 2 - 20, weather_y + margin_top +
            weather_line1_height +
            weather_line_spacing +
            weather_line2_height +
            weather_line_spacing +
            weather_line3_height +
            weather_line_spacing +
            weather_line4_height +
            weather_line_spacing + 10, u'Hava Kalitesi')

if wdata.get('today_temp_hig'):
    fmt = u'{today_temp_hig}~{today_temp_low}℃ {current_wind}'
else:
    fmt = u'{today_temp_low}℃ {current_wind}'
msg = fmt.format(**wdata)
screen.text(weather_text_x + 64, weather_y + margin_top
            + weather_line1_height + weather_line_spacing + 5, msg)
weather2_x = 550
weather2_y = (weather_y + margin_top +
              weather_line1_height +
              weather_line_spacing +
              weather_line2_height +
              weather_line_spacing)

# Çerçeve çiz
box_height = 210
box_width = screen_width - 20 - weather2_x
screen.line(weather2_x, weather2_y, screen_width - 20, weather2_y)
screen.line(weather2_x, weather2_y + 48 + 10, screen_width - 20, weather2_y + 48 + 10)
screen.line(weather2_x, weather2_y, weather2_x, weather2_y + box_height)
screen.line(screen_width - 20, weather2_y, screen_width - 20, weather2_y + box_height)
screen.line(weather2_x, weather2_y + box_height, screen_width - 20, weather2_y + box_height)

screen.set_ch_font_size(FONT_SIZE_32)
screen.set_en_font_size(FONT_SIZE_32)
screen.text(weather2_x + 50, weather2_y + 12, u'Yarın Tahmini')

fmt = u'{tomorrow_weather},{tomorrow_temp_hig}~{tomorrow_temp_low}℃,{tomorrow_wind}'
msg = fmt.format(**wdata)
if wdata.get('tomorrow_aq'):
    msg += u', AQI {tomorrow_aq}{tomorrow_aq_desc}'.format(**wdata)
screen.wrap_text(weather2_x + 8, weather2_y + 48 + 20, box_width, msg)

screen.update()
screen.disconnect()
