import os
import json
import asyncio
from websockets.client import connect

# Get the directory containing this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (two levels up)
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

async def test_chat():
    # Load configuration from project root
    config_path = os.path.join(PROJECT_ROOT, "config.json")
    with open(config_path) as f:
        config = json.load(f)

    uri = f"ws://{config['backend']['host']}:{config['backend']['port']}/chat"
    os.system('clear')
    
    async with connect(uri) as websocket:
        # Send test message
        msg = 'which rag system is Roman using?'#input('Enter your message: ')
        print(f'Sending message: {msg}')
        message = {
            "type": "message",
            "content": msg
        }
        await websocket.send(json.dumps(message))
        
        # Keep receiving messages until we get the final response
        while True:
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data["type"] == "status":
                print(f"Status: {response_data['content']}")
            elif response_data["type"] == "message":
                print("\nResponse:")
                print(response_data['content'])
                break
            elif response_data["type"] == "error":
                print(f"\nError: {response_data['content']}")
                break

if __name__ == "__main__":
    try:
        asyncio.run(test_chat())
    except KeyboardInterrupt:
        print("\nChat terminated by user")
    except Exception as e:
        print(f"\nError: {str(e)}") 