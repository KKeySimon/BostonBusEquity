import os
import asyncio
import time
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import pyppeteer

# Set the environment variable early
os.environ["PYPPETEER_CHROME_EXECUTABLE"] = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Monkey-patch pyppeteer.launch to force the executablePath parameter
_original_launch = pyppeteer.launch
async def patched_launch(*args, **kwargs):
    kwargs['executablePath'] = os.environ["PYPPETEER_CHROME_EXECUTABLE"]
    return await _original_launch(*args, **kwargs)
pyppeteer.launch = patched_launch

url = "https://www.ctps.org/dv/mbtasurvey2018/index.html#navButton"
session = HTMLSession()
response = session.get(url)

# Render the page and simulate clicking the different tabs.
click_script = "document.getElementById('oth_demo').click();" # Change this to the appropriate ID for the tab you want to click
response.html.render(script=click_script, timeout=20)

# Wait a bit for the fare data to load after the click
time.sleep(20) # Needed to change to 20 to load everything

# Save HTML for debugging
with open("rendered_tab.html", "w", encoding="utf-8") as f:
    f.write(response.html.html)

soup = BeautifulSoup(response.html.html, 'html.parser')
text_elements = soup.select("text.chartNum")
print("Found", len(text_elements), "text elements with class 'chartNum'")

data = []
for text_el in text_elements:
    classes = text_el.get("class", [])
    route = None
    # Look for the class that starts with 'r' (excluding "chartNum")
    for cls in classes:
        if cls != "chartNum" and cls.startswith("r"):
            route = cls[1:]  # Remove the "r" prefix
            break
    if route:
        percent = text_el.get_text(strip=True)
        data.append((route, percent))

# Sort the data
data_sorted = sorted(data, key=lambda tup: (0 if "line-all" in tup[0].lower() else 1, tup[0]))

# Write the sorted data
output_filename = "other_demographics_data.txt" # Change the filename as necessary
with open(output_filename, "w", encoding="utf-8") as file:
    for route, percent in data_sorted:
        file.write(f"Route {route}: {percent}\n")

print(f"Fare data saved to {output_filename}")