# AI assisted development stages

## Stage 1: optionally work directly via touchy-pad API

Originally this project talked to the StreamController app to do its work.  I'd now like it to default to talking to touchy-pad devices instead. (but add a --streamcontroller cli flag to tell it to use the old StreamController API instead)

Changes:
* Change pyproject.py to reference touchy-pad python library (currently during development just point to touchy-pad/app but eventually via touchy-pad pypi entry)
* make a new mostly abstract baseclass from StreamControllerClient in api-client.  Some operations in that base class will need alternative implementations in the new TouchyApiClient subclass.  Hopefuly only a few operations are actually needed to be reimplmented
* move StreamControllerClient from api-client.py into sc-api-client.py
* make a new src/autopage/touchy submodule.  Put TouchyApiClient in there.
* toml_to_jsonpage currently generates json which is formated for StreamController, in the plan propose an elegant alternative refactoring so that when we are using
* refer to touchy-pad/src/touchy-pad/pages/test.py and touchy-pad/docs/python-api.md for example usage of the python API.  You'll want to create 'uscrs' similar to what the touchy-pad/src/touchy-pad/touchydeck/layout.py is doing (but use ImageButton widgets instead)
* TouchyApiClient will need to be smart about a few things
  * Eventually we'll want to add automatic icon selection from the Material Design icon library (but not yet) - for now just use a placeholder icon for all buttons
  * You'll want to tile ImageButtons across the uscr (72x72 pixel buttons based on what the screen can hold - similar to touchydeck)
  * The various autopage .toml actions (such as "actions = [ { type = "+Cut" } ]") can be mapped to Macro actions on the ImageButton you create.
