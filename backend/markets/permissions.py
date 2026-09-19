from companies.permissions import can_update, get_membership


def can_update_market(user, market):
    return can_update(get_membership(user, market.company))
