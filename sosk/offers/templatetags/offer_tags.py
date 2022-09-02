from django import template
register = template.Library()

import random

def choice_buttons(choice):
    return [
    ('<button type="submit" value="1" name="choose_self" class="chooser"><span>I get <strong>%s</strong></span></button>' % to_currency(choice.self_offer)),
    ('<button type="submit" value="1" name="choose_other" class="chooser"><span>Other person gets <strong>%s</strong></span></button>' % to_currency(choice.other_offer))
    ]
    
def random_buttons(choice):
    buttons = choice_buttons(choice)
    random.shuffle(buttons)
    return " ".join(buttons)

# EDITED CURRENCY TO BE IN POINTS.
def to_currency(cents):
    return "%d" % (int(cents))
    
def result_button(choice, for_self = False):
    """ Create a button that looks like:
    <button type="button" class = "chooser" id="notchosen" disabled="disabled">I get <strong>$5.13</strong></button>
    """
    id_text = "chosen"
    if not choice.chose_self == for_self:
        id_text = "notchosen"
    
    button_text = "I get"
    amt = to_currency(choice.self_offer)
    if not for_self:
        button_text = "Other person gets"
        amt = to_currency(choice.other_offer)
    
    return '<button type="button" class = "chooser" id="%s" disabled="disabled">%s <strong>%s</strong></button>' % (id_text, button_text, amt)
    
def result_text(choice):
    if choice.chose_self:
        return "You will get %s." % to_currency(choice.self_offer)
    else:
        return "A stranger will get %s." % to_currency(choice.other_offer)

register.simple_tag(random_buttons)
register.simple_tag(result_button)
register.simple_tag(result_text)
