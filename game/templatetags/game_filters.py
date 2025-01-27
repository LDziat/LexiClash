# game/templatetags/game_filters.py

from django import template

register = template.Library()

@register.filter
def get_tile(tiles, coords):
    x, y = coords
    return tiles.filter(x=x, y=y).first()

@register.simple_tag
def make_range(value):
    return range(value)
