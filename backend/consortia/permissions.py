from companies.permissions import can_update, get_membership


def can_manage_consortium(user, consortium):
    return can_update(get_membership(user, consortium.owner_company))


def can_read_consortium(user, consortium):
    if user.is_superuser:
        return True
    return consortium.members.filter(company__memberships__user=user, company__memberships__active=True, active=True).exists()
