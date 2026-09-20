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


def can_read_global_resources(user):
    """Global business references remain behind the application's Membership boundary."""
    return user.is_superuser or Membership.objects.filter(user=user, active=True).exists()
