from src.settings import CRAFTING_RECIPES


def can_craft(recipe, inventory):
    for item_id, needed in recipe["ingredients"].items():
        if inventory.count_item(item_id) < needed:
            return False
    return True


def do_craft(recipe, inventory, tool_manager=None):
    """Perform crafting. Returns True on success."""
    if not can_craft(recipe, inventory):
        return False

    # Remove ingredients
    for item_id, needed in recipe["ingredients"].items():
        inventory.remove_item(item_id, needed)

    # Grant result
    if recipe["result_type"] == "tool":
        if tool_manager:
            tool_manager.add_tool(recipe["result"])
        return True
    else:
        return inventory.add_item(recipe["result"], 1)
