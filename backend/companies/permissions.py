from .models import Membership


def get_membership(user, company):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return "OWNER"
    membership = Membership.objects.filter(user=user, company=company, active=True).first()
    return membership.role if membership else None


def can_update(role):
    return role in {Membership.Role.OWNER, Membership.Role.ADMIN}
