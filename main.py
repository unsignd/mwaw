from AppKit import NSWorkspace, NSScreen
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from io import BytesIO
import urllib.request, glob, subprocess, threading, os

# Define the path the converted image will be saved to

# Define fonts
titleFont = ImageFont.truetype(BytesIO(open('fonts/Pretendard-ExtraBold.ttf', 'rb').read()), 20)
artistFont = ImageFont.truetype(BytesIO(open('fonts/Pretendard-Medium.ttf', 'rb').read()), 12)

# Get the current wallpaper
workspace = NSWorkspace.sharedWorkspace()
screen = NSScreen.mainScreen()

screen_width, screen_height = screen.frame().size

# Calculate the size and position of the panel
rect_width = int(screen_width * 0.18)
rect_height = int(screen_width * 0.05)
rect_x = int((screen_width - rect_width) / 2)
rect_y = int((screen_height - rect_height) / 2)
corner_radius = 20

past_image = ''

def draw_cover(draw, gap, fill=None):
  draw.pieslice((0, 0, corner_radius, corner_radius), start=180, end=270, fill=fill)
  draw.pieslice((rect_height - gap - corner_radius, 0, rect_height - gap, corner_radius), start=270, end=360, fill=fill)
  draw.pieslice((rect_height - gap - corner_radius, rect_height - gap - corner_radius, rect_height - gap, rect_height - gap), start=0, end=90, fill=fill)
  draw.pieslice((0, rect_height - gap - corner_radius, corner_radius, rect_height - gap), start=90, end=180, fill=fill)

  # Draw the straight sides
  draw.rectangle((corner_radius / 2 + 1, 0, rect_height - gap - corner_radius / 2, corner_radius / 2), fill=fill)
  draw.rectangle((corner_radius / 2 + 1, rect_height - gap, rect_height - gap - corner_radius / 2, rect_height - gap - corner_radius / 2), fill=fill)
  draw.rectangle((0, corner_radius / 2 + 1, corner_radius / 2, rect_height - gap - corner_radius / 2), fill=fill)
  draw.rectangle((rect_height - gap, corner_radius / 2 + 1, rect_height - gap - corner_radius / 2, rect_height - gap - corner_radius / 2), fill=fill)
  draw.rectangle((corner_radius / 2 + 1, corner_radius / 2 + 1, rect_height - gap - corner_radius / 2 - 1, rect_height - gap - corner_radius / 2 - 1), fill=fill)

def draw_panel(draw, fill=None):
  draw.pieslice((rect_x, rect_y, rect_x + corner_radius * 2, rect_y + corner_radius * 2), start=180, end=270, fill=fill)
  draw.pieslice((rect_x + rect_width - corner_radius * 2, rect_y, rect_x + rect_width, rect_y + corner_radius * 2), start=270, end=360, fill=fill)
  draw.pieslice((rect_x + rect_width - corner_radius * 2, rect_y + rect_height - corner_radius * 2, rect_x + rect_width, rect_y + rect_height), start=0, end=90, fill=fill)
  draw.pieslice((rect_x, rect_y + rect_height - corner_radius * 2, rect_x + corner_radius * 2, rect_y + rect_height), start=90, end=180, fill=fill)

  # Draw the straight sides
  draw.rectangle((rect_x + corner_radius + 1, rect_y, rect_x + rect_width - corner_radius - 1, rect_y + corner_radius), fill=fill)
  draw.rectangle((rect_x + corner_radius + 1, rect_y + rect_height, rect_x + rect_width - corner_radius - 1, rect_y + rect_height - corner_radius), fill=fill)
  draw.rectangle((rect_x, rect_y + corner_radius + 1, rect_x + corner_radius, rect_y + rect_height - corner_radius - 1), fill=fill)
  draw.rectangle((rect_x + rect_width, rect_y + corner_radius + 1, rect_x + rect_width - corner_radius, rect_y + rect_height - corner_radius - 1), fill=fill)
  draw.rectangle((rect_x + corner_radius + 1, rect_y + corner_radius + 1, rect_x + rect_width - corner_radius - 1, rect_y + rect_height - corner_radius - 1), fill=fill)

def interval():
  global past_image

  image = Image.open(glob.glob('./wallpaper/*')[0])
  image = image.resize((int(screen_width), int(screen_height)), Image.Resampling.LANCZOS)

  # Draw the panel on the image
  draw = ImageDraw.Draw(image, 'RGBA')

  draw_panel(draw, fill=(0, 0, 0, 255))

  # Create rounded rectangle mask
  mask = Image.new('L', (int(screen_width), int(screen_height)))
  draw_mask = ImageDraw.Draw(mask)
  draw_panel(draw_mask, fill='#b8bbd0')

  # Blur image
  blurred = image.filter(ImageFilter.BoxBlur(200))

  image.paste(blurred, mask=mask)

  # Get the song info using AppleScript
  track_artist = subprocess.run(['osascript', '-e', 'tell application "Spotify" to artist of current track'], capture_output=True).stdout
  track_title = subprocess.run(['osascript', '-e', 'tell application "Spotify" to name of current track'], capture_output=True).stdout
  track_cover = subprocess.run(['osascript', '-e', 'tell application "Spotify" to artwork url of current track'], capture_output=True).stdout
  track_id = subprocess.run(['osascript', '-e', 'tell application "Spotify" to id of current track'], capture_output=True).stdout

  song_artist = f"{track_artist[:-1]}"[2:-1];
  song_title = f"{track_title[:-1]}"[2:-1];
  song_cover = f"{track_cover[:-1]}"[2:-1];
  song_id = f"{track_id[:-1]}"[2:-1];

  image_path = f'./{song_id}.png'


  # Get an album cover image from a url
  file = BytesIO(urllib.request.urlopen(song_cover).read())

  cover = Image.new('RGBA', (rect_height - 28, rect_height - 28), (0, 0, 0, 0))
  cover = cover.resize((rect_height - 28, rect_height - 28), Image.Resampling.LANCZOS)
  dcover = ImageDraw.Draw(cover)

  draw_cover(dcover, 28, fill='#fff')

  cover.paste((Image.open(file).resize((rect_height - 28, rect_height - 28), Image.Resampling.LANCZOS)), mask=cover)
  image.paste(cover, (rect_x + 14, rect_y + 14), cover)

  if titleFont.getlength(song_title) <= rect_width - rect_height - 20:
    draw.text((rect_x + rect_height + 5, rect_y + 20), rf'{song_title}', font=titleFont, fill='#fff')
  else:
    for i in range(len(song_title) + 1):
      if titleFont.getlength(song_title[:i] + "..") > rect_width - rect_height - 20:
        if i == 0:
          draw.text((rect_x + rect_height + 5, rect_y + 20), '..', font=titleFont, fill='#fff')
        else:
          draw.text((rect_x + rect_height + 5, rect_y + 20), rf'{song_title[:i - 1]}..', font=titleFont, fill='#fff')

        break

  if artistFont.getlength(song_artist) <= rect_width - rect_height - 20:
    draw.text((rect_x + rect_height + 5, rect_y + 48), rf'{song_artist}', font=artistFont, fill='#fff')
  else:
    for i in range(len(song_artist) + 1):
      if titleFont.getlength(song_artist[:i] + "..") > rect_width - rect_height - 20:
        if i == 0:
          draw.text((rect_x + rect_height + 5, rect_y + 48), '..', font=artistFont, fill='#fff')
        else:
          draw.text((rect_x + rect_height + 5, rect_y + 48), rf'{song_artist[:i - 1]}..', font=artistFont, fill='#fff')

        break

  # Save the image as a PNG file
  image.save(image_path)
  os.system(f"osascript -e \'tell application \"Finder\" to set desktop picture to \"{os.path.abspath(image_path)}\" as POSIX file\'")

  if past_image != '':
    os.remove(past_image)

  past_image = image_path

  track_artist = ''
  track_title = ''
  track_cover = ''
  track_id = ''
  song_artist = ''
  song_title = ''
  song_cover = ''
  song_id = ''

  # Recursively call the function every second
  threading.Timer(1, interval).start()

interval()