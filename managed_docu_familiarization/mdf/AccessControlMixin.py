import logging
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseForbidden


class AccessControlMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """"
    Mixin that extends access control by requiring user authentication,
    specific permissions, and optional group membership. This also includes logging
    and access testing for additional flexibility.
    """
    group_required = None  # Define required group(s) for access
    permission_required = []  # Permissions required for access
    logger = logging.getLogger(__name__)

    def check_permissions(self, request):
        """
        Check if the user has the required permissions for this view.
        Override this method in the view to implement specific permission logic.
        """
        return True  # Return True by default, override in the view if needed

    def log_user_activity(self, request):
        """
        Log basic user activity like login status and role-based actions.
        """
        user = request.user
        self.logger.info(f"User '{user.zf_id}' is accessing '{request.path}'")

    def test_user_access(self, request):
        """
        Test if the user has access to the view.
        This method can be overridden in the view to add additional checks.
        """
        if not request.user.is_authenticated:
            self.logger.warning(f"Unauthorized access attempt by {request.user.username}")
            return HttpResponseForbidden("You are not authorized to view this page.")

        # Check if the user has the required permissions
        if self.permission_required and not request.user.has_perms(self.get_permission_required()):
            self.logger.warning(f"User '{request.user.username}' does not have the required permissions.")
            return HttpResponseForbidden("You do not have the necessary permissions to access this page.")

        # Check if the user belongs to the required group(s)
        if self.group_required:
            if isinstance(self.group_required, str):
                # If a single group is provided as a string, convert it to a list
                groups = [self.group_required]
            else:
                # If multiple groups are provided, use them directly
                groups = self.group_required

            # Verify if the user is a member of at least one of the required groups
            if not request.user.groups.filter(name__in=groups).exists():
                self.logger.warning(f"User '{request.user.zf_id}' does not belong to the required group(s).")
                return HttpResponseForbidden("You do not have the required group membership to access this page.")

        return None  # No issues, proceed with the request

    def get_permission_required(self):
        """
        Get the permission required for the view, can be overridden in the view.
        This method returns a list of permissions that are required for the view.
        """
        return self.permission_required

    def check_user__groups(self, request):
        """
        Check if the user is in the required groups for this view.
        """
        return True
