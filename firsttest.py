from urllib.request import urlopen
import re

url = "http://cnn.com"
page = urlopen(url)
html_bytes = page.read()
html = html_bytes.decode("utf-8")

pattern = "<span class=\"container__headline-text\" data-editable=\"headline\">.*?</span>"

match_results = re.findall(pattern, html, re.IGNORECASE)

match_results = [re.sub("<.*?>", "", element) for element in match_results]

print(match_results)