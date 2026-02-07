# Example usage of api-client

```
(.venv) ubuntu@0a7dfd9590dc:/workspaces/StreamController/localdev/autopage/src/autopage$ python api_client.py controllers
fake-deck-1
fake-deck-2
```

```
(.venv) ubuntu@0a7dfd9590dc:/workspaces/StreamController/localdev/autopage/src/autopage$ python api_client.py pages      
second
test
```

```
(.venv) ubuntu@0a7dfd9590dc:/workspaces/StreamController/localdev/autopage/src/autopage$ python api_client.py icon-packs
com_core447_MaterialIcons
```

```
(.venv) ubuntu@0a7dfd9590dc:/workspaces/StreamController/localdev/autopage/src/autopage$ python api_client.py icons     
usage: api_client.py icons [-h] pack_id
api_client.py icons: error: the following arguments are required: pack_id
(.venv) ubuntu@0a7dfd9590dc:/workspaces/StreamController/localdev/autopage/src/autopage$ python api_client.py icons com_core447_MaterialIcons 
... (many entries omitted for brevity)
no_meals
no_meals_ouline-inv
no_meals_ouline
no_meeting_room-inv
no_meeting_room
no_photography-inv
no_photography
north-inv
north
north_east-inv
north_east
north_west-inv
north_west
... (omitted for brevity)
zoom_in-inv
zoom_in
zoom_in_map-inv
zoom_in_map
zoom_out-inv
zoom_out
zoom_out_map-inv
zoom_out_map
```