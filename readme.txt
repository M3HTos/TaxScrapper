Python version: 3.8
Chrome version used by driver: 90

You can download driver for another version of Chrome from https://chromedriver.chromium.org/downloads

To run the script, you must specify action and arguments in input.json.

For information about taxes forms use pattern:
{
    "action": "Get taxes form info",
    "args": {
        "forms": [*]
    }
}
* - list of needed forms. Each form must be quoted and separated by a comma.
The information will be written to "taxes.json"

For downloading PDF files use pattern:
{
    "action": "Download PDF",
    "args": {
        "name": "Form W-2AS",
        "range": "2020-2021"
  }
}