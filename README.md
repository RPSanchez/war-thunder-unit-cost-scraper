# War Thunder Unit Cost Scraper
A silly little Python scraper I made to extract and aggregate the total Golden Eagle (GE) cost, including Talisman and crew ace (Aces) costs, of all units listed in War Thunder's official wiki tech trees. The script respects server rate limits by throttling requests and retrying on failure, providing detailed progress and error logging. Supports aviation, helicopters, ground, ships, and boats categories.

## 📦 Installation
Ensure Python 3.9 or higher is installed.

Install dependencies with:
```
pip install requests beautifulsoup4
```

## 🚀 Usage
Run the script:
```
python warthunder_unit_cost_scraper.py
```
What it does:
- Parses all unit URLs from the War Thunder Wiki tech trees
- Visits each unit page to extract GE costs
- Adds Talisman and Aces costs together
- Logs per-unit costs and missing data
- Displays a cumulative GE total for all vehicles
- Includes retry logic and throttling to prevent rate-limiting
> ⚠️ Estimated runtime: 7–10 minutes, due to server-friendly throttling.

## 📝 License
Licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

## 🙏 Acknowledgements
- [War Thunder Wiki](https://wiki.warthunder.com/) – for hosting unit data
- [Gaijin Entertainment](https://warthunder.com/en) – for creating War Thunder
