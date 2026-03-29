import traceback
try:
    exec(open('scraper/parse_sitemap.py').read())
except Exception as e:
    traceback.print_exc()
