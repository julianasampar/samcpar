# Import libraries
from mcp.server.fastmcp import FastMCP
from fastmcp.prompts import Message
from mcp.types import ToolAnnotations

# Getting notification tools
from tools import notifier_tools

# Create an MCP
mcp = FastMCP("system_notifier", log_level="ERROR")

# Adding the already defined tools to the MCP
mcp.add_tool(
    notifier_tools.get_current_datetime,
    name="get_current_datetime",
    description="Returns the current date and time formatted according to the specified format",
    annotations=ToolAnnotations(
        title="Get Current Date and Time",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True
    )

)

mcp.add_tool(
    notifier_tools.add_duration_to_datetime,
    name="add_duration_to_datetime",
    description="Adds a specified duration to a datetime string and returns the resulting datetime in a detailed format. This tool converts an input datetime string to a Python datetime object, adds the specified duration in the requested unit, and returns a formatted string of the resulting datetime. It handles various time units including seconds, minutes, hours, days, weeks, months, and years, with special handling for month and year calculations to account for varying month lengths and leap years. The output is always returned in a detailed format that includes the day of the week, month name, day, year, and time with AM/PM indicator (e.g., 'Thursday, April 03, 2025 10:30:00 AM').",
    annotations=ToolAnnotations(
        title="Add Duration to Date and Time",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False
    )
)

mcp.add_tool(
    notifier_tools.schedule_notification,
    name="schedule_notification",
    description="Schedule a desktop notification with title and content to appear after a specified delay.",
    annotations=ToolAnnotations(
        title="Add Duration to Date and Time",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False
    )
)

@mcp.resource("resource://interests/{topic}")
def get_interest(topic: str) -> str:
    interests = {
        'Politics': 'Latest political news and updates',
        'Economics': 'Economic indicators and analysis',
        'International Affairs': 'Latest updates on countries affairs',
        'Sports': 'Latest news on Sports events and results',
        'Business': 'Relevant updates about companies, acquisitions and stocks',
    }
    return interests.get(topic, "Topic not found")


@mcp.prompt()
def notify_me_latest_news(interests: str) -> str:
    """Generates a news reporter prompt focused on the user's interests."""
    prompt = f"""
        <role> 
        You are a news reporter. Your role is to create OS Notifications to report the latest news.
        Extract away any HTML or XML tags within the text. Report only the text itself.
        The content must fit into the size (320 pixels x 340 pixels) banner.
        One notification must report only one news.
        Set notification title as being: "TIME FOR YOUR NEWS!!!!"
        Focus on news about: {interests}
        </role>
        <example>
        TIME FOR YOUR NEWS!!!
        IRAN-ISRAEL CONFLICT ESCALATES
        Iran suspends peace talks with US and threatens to open "other fronts" 
        in the war. Israel intercepts projectiles from Lebanon as tensions spike
        over ceasefire violations. Trump claims talk continues at a "rapid pace"
        despite continuous Iranian threats.
        </example>
    """
    return [Message(role="user", content=prompt)]

if __name__ == "__main__":
    mcp.run()