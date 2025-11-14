import random
from fastmcp import FastMCP
import json

# Create a FastMCP server instance
mcp = FastMCP(name="Simple Calculator Server")

@mcp.tool()
def roll_dice(n_dice: int = 1) -> list[int]:
    """Roll n_dice 6-sided dice and return the results."""
    return [random.randint(1, 6) for _ in range(n_dice)]

@mcp.tool()
def random_number(min_val: int = 1, max_val: int = 100) -> int:
    """Get random number between min number and max number."""
    return random.randint(min_val,max_val)

@mcp.resource('info://server')
def server_info() -> str:
    info = {
        'name': 'Simple Calculator Server',
        'version':'1.0.0',
        'description':'A basic MCP server with math tools',
        'tools':['add','random_number'],
        'author':'Vivek M'
    }       
    
    return json.dumps(info,indent=2)

if __name__ == "__main__":
    mcp.run(transport='http',host='0.0.0.0',port=8000)
