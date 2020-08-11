# Export your card collection from MTG: Arena
If you want to use just the pre-built Windows executable, there are no pre-requisites.

Otherwise you will need to install [mtgatracker/python-mtga](https://github.com/mtgatracker/python-mtga) to use the export tool.
You can try following forks, if the original python-mtga module fails:
 - [kelesi/python-mtga](https://github.com/kelesi/python-mtga/tree/logging)
 - [pak21/python-mtga](https://github.com/pak21/python-mtga)

#### Note:
mtga-export reads the MTGA/Unity log file located under: 
    
    "%AppData%\LocalLow\Wizards Of The Coast\MTGA\Player.log"

In order for this export tool to work, "Detailed Logs (Plugin Support)" must be enabled in MTGA's Options / Account screen.
If the MTGA game developers stop logging to this file, this export tool will not work anymore.

## Quick installation without python on Windows
Just download the standalone windows [latest](https://github.com/kelesi/mtga-utils/releases/latest) pre-built executable from [releases](https://github.com/kelesi/mtga-utils/releases).

### Run it from cmd
Export your collection in [mtggoldfish](https://www.mtggoldfish.com/help/import_formats#mtggoldfish) format:

`mtga-export.exe --goldfish -f mtga_collection_goldfish.csv`

Export your collection in [deckstats](https://www.mtggoldfish.com/help/import_formats#deckstats) format:

`mtga-export.exe --deckstats -f mtga_collection_deckstats.csv`

Your collection will be saved to the current folder into mtga_collection_goldfish.csv or mtga_collection_deckstats.csv, which you can use to  import into mtggoldfish.com or deckstats.net.

## Examples:
Export your collection in [mtggoldfish](https://www.mtggoldfish.com/help/import_formats#mtggoldfish) format:

`mtga-export.py --goldfish -f mtga_collection_goldfish.csv`

Export your collection in [deckstats](https://www.mtggoldfish.com/help/import_formats#deckstats) format:

`mtga-export.py --deckstats -f mtga_collection_deckstats.csv`


## General usage:

```
usage: mtga-export.py [-h] [-v] [-l LOG_FILE] [-k KEYWORD] [--collids] [-c]
                      [-e {name,pretty_name,cost,sub_types,set,set_number,card_type,mtga_id,count} [{name,pretty_name,cost,sub_types,set,set_number,card_type,mtga_id,count} ...]]
                      [-gf] [-ds] [-ct] [-i] [-ij] [--decks] [--decksjson]
                      [--decknames] [--deckinfo DECK_NAME]
                      [--deckexport DECK_NAME] [-f FILE] [--log [LOG]]

Parse MTGA log file

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -l LOG_FILE, --log_file LOG_FILE
                        MTGA/Unity log file [Win: %AppData%\LocalLow\Wizards
                        Of The Coast\MTGA\output_log.txt]
  -k KEYWORD, --keyword KEYWORD
                        List json under keyword
  --collids             List collection ids
  -c, --collection      List collection with card data
  -e {name,pretty_name,cost,sub_types,set,set_number,card_type,mtga_id,count} [{name,pretty_name,cost,sub_types,set,set_number,card_type,mtga_id,count} ...], --export {name,pretty_name,cost,sub_types,set,set_number,card_type,mtga_id,count} [{name,pretty_name,cost,sub_types,set,set_number,card_type,mtga_id,count} ...]
                        Export collection in custom format
  -gf, --goldfish       Export in mtggoldfish format
  -ds, --deckstats      Export in deckstats format
  -ct, --completiontracker
                        Export set completion
  -i, --inventory       Print inventory
  -ij, --inventoryjson  Print inventory as json
  --decks               Print user decks
  --decksjson           Print user decks as json
  --decknames           Print names of user's decks
  --deckinfo DECK_NAME  Print info about specific deck
  --deckexport DECK_NAME
                        Export specific deck in Arena format
  -f FILE, --file FILE  Store export to file
  --log [LOG]           Log level
  ```
