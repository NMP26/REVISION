from companies.permissions import can_update, get_membership


def can_update_market(user, market):
    if user.is_superuser:
        return True
    if market.holder_type == market.HolderType.CONSORTIUM:
        return market.consortium.members.filter(active=True, company__memberships__user=user, company__memberships__active=True, company__memberships__role__in=["OWNER", "ADMIN"]).exists()
    return can_update(get_membership(user, market.company))


def market_role(user, market):
    if user.is_superuser:
        return "OWNER"
    if market.holder_type == market.HolderType.CONSORTIUM:
        roles = list(market.consortium.members.filter(active=True, company__memberships__user=user, company__memberships__active=True).values_list("company__memberships__role", flat=True))
        for role in ("OWNER", "ADMIN", "MEMBER"):
            if role in roles:
                return role
        return None
    membership = market.company.memberships.filter(user=user, active=True).first()
    return membership.role if membership else None
