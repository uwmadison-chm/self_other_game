from django import template
register = template.Library()

import random

def choice_buttons(choice):
    """
    Choosing 'self' or 'other' indicates that the choice *benefits* self or
    other, respectively.
    """
    return [
    ('<button type="submit" value="1" name="choose_other" class="chooser"><span>I lose <strong>%s</strong></span></button>' % to_currency(choice.self_offer)),
    ('<button type="submit" value="1" name="choose_self" class="chooser"><span>Other person loses <strong>%s</strong></span></button>' % to_currency(choice.other_offer))
    ]
    
def random_buttons(choice):
    buttons = choice_buttons(choice)
    random.shuffle(buttons)
    return " ".join(buttons)

def to_currency(cents):
    return "$%d.%02d" % (int(cents/100), int(cents%100))
    
def result_button(choice, for_self = False):
    """ Create a button that looks like:
    <button type="button" class = "chooser" id="notchosen" disabled="disabled">I lose <strong>$5.13</strong></button>
    """
    id_text = "chosen"
    if not choice.chose_self == for_self:
        id_text = "notchosen"
    
    button_text = "I lose "
    amt = to_currency(choice.self_offer)
    if not for_self:
        button_text = "Other person loses"
        amt = to_currency(choice.other_offer)
    
    return '<button type="button" class = "chooser" id="%s" disabled="disabled">%s <strong>%s</strong></button>' % (id_text, button_text, amt)
    
def result_text(choice):
    if choice.chose_self:
        return "You will lose %s." % to_currency(choice.self_offer)
    else:
        return "A stranger will lose %s." % to_currency(choice.other_offer)

register.simple_tag(random_buttons)
register.simple_tag(result_button)
register.simple_tag(result_text)
