from django.contrib import admin
from django.contrib.auth import get_user_model
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import escape
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from managed_docu_familiarization.users.forms import UserChangeForm
from managed_docu_familiarization.users.forms import UserCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    fieldsets = (
        (None, {
            'fields': (
                ('zf_id', 'email'),
            ),
        }),
        ('Personal info', {
            'fields': (
                ('first_name', 'last_name'),
            ),
        }),
        ('Account', {
            'fields': (
                ('is_staff',),
            ),
        }),
        ('Permissions', {
            'fields': (
                ('user_permissions', 'groups',),
            ),
        }),
    )

    list_display = [
        'zf_id',
        'first_name',
        'last_name',
        'email',
        'last_login',
        'get_staff_status',
    ]

    list_filter = [
        'is_staff',
        'last_login',
    ]

    search_fields = [
        'zf_id',
        'first_name',
        'last_name',
    ]

    filter_horizontal = [
        'groups',
        'user_permissions'
        ]

    def get_staff_status(self, obj):
        return obj.is_staff

    def get_form(self, request, obj=None, **kwargs):
        """overrides some fields for permissions

        https://realpython.com/manage-users-in-django-admin/#django-admin-and-model-permissions
        """
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()

        # # https://realpython.com/manage-users-in-django-admin/#grant-permissions-only-using-groups
        if not is_superuser:
            disabled_fields |= {
                'username',
                'is_superuser',
            }

        # Prevent non-superusers from editing their own permissions
        if (
            not is_superuser
            and obj is not None
            and obj == request.user
        ):
            disabled_fields |= {
                # 'is_staff',
                'is_superuser',
                'groups',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


@admin.register(admin.models.LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Monitor all user activity."""

    date_hierarchy = 'action_time'

    list_filter = [
        'action_flag',
        ('content_type', admin.RelatedOnlyFieldListFilter),
        ]

    search_fields = [
        'object_repr',
        'change_message',
        'user__zf_id',
        'user__first_name',
        'user__last_name',
        ]

    list_display = [
        '__str__',
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
        # 'action_flag_ico',
        ]

    # override all permissions, only allow superusers to view

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def object_link(self, obj):
        if obj.action_flag == admin.models.DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = '<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
                )
        return mark_safe(link)

    object_link.admin_order_field = "object_repr"
    object_link.short_description = _("object")

    def action_flag_ico(self, obj):

        action_icons = {
            admin.models.ADDITION: static('admin/img/icon-addlink.svg'),
            admin.models.CHANGE  : static('admin/img/icon-changelink.svg'),
            admin.models.DELETION: static('admin/img/icon-deletelink.svg'),
            }

        return format_html(f'<img src="{action_icons[obj.action_flag]}"> {obj.action_flag}')

    def get_queryset(self, request):
        return super(LogEntryAdmin, self).get_queryset(request) \
            .select_related('user', 'content_type')
