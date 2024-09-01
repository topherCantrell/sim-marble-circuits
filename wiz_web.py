import time
import board
import digitalio
import biplane
import asyncio

server = biplane.Server()

@server.route("/", "GET")
def do_root(query_parameters, headers, body):

  with open('index.html') as f:
    content = f.read()
  return biplane.Response(content, content_type="text/html")

@server.route("/desk", "GET")
def do_desk(query_parameters, headers, body):
  return biplane.Response("<b>Hello, world!</b>", content_type="text/html")

async def run_server():
  for _ in server.circuitpython_start_wifi_station("TopherNet", "NetTopher1","app"):
    await asyncio.sleep(0)  # let other tasks run

async def blink_builtin_led():  
    while True:
      print('HERE')
      await asyncio.sleep(2)

asyncio.run(asyncio.gather(blink_builtin_led(), run_server()))  # run both coroutines at the same time
