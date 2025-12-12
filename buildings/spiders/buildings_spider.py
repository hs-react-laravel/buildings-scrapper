from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

import scrapy
import csv

class BuildingsSpider(scrapy.Spider):
    name = "buildings"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_rows = []

    async def start(self):
        with open("buildings.csv", newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
        
        for row in rows:
            row["Property Type"] = ""
            url = "https://www.miamidade.gov/Apps/RER/EPSPortal/PlanReview/BRApplication/Details/" + row["Case Number"]
            yield scrapy.Request(url=url, callback=self.parse, meta={"row": row})

    def parse(self, response):
        row = response.meta["row"]
        soup = BeautifulSoup(response.body, "html.parser")
        label = soup.find("label", {"for": "PropertyType"})
        td = label.find_parent("td")
        next_td = td.find_next_sibling("td")

        property_type = next_td.decode_contents()
        row["Property Type"] = property_type if property_type else "Unknown"
        self.all_rows.append(row)
    def closed(self, reason):
        # Group rows by Property Type
        grouped_rows = defaultdict(list)
        for row in self.all_rows:
            grouped_rows[row.get("Property Type", "Unknown")].append(row)

        # Save each group as separate CSV
        for prop_type, rows in grouped_rows.items():
            filename = f"{prop_type.replace(' ', '_')}.csv"
            headers = rows[0].keys() if rows else []
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            self.logger.info(f"Saved {len(rows)} rows to {filename}")

