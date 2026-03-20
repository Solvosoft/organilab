import json

from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe

from auth_and_perms.models import ProfilePermission
from presentation.models import Tutorial, TutorialProgress

register = template.Library()


def _get_user_rol_ids(user, org_pk):
    """Get the set of Rol IDs the user has in the given organization."""
    if not user.is_authenticated or not org_pk:
        return set()
    try:
        from laboratory.models import OrganizationStructure
        org_ct = ContentType.objects.get_for_model(OrganizationStructure)
        profile_perms = ProfilePermission.objects.filter(
            profile=user.profile,
            content_type=org_ct,
            object_id=org_pk,
        )
        rol_ids = set()
        for pp in profile_perms:
            rol_ids.update(pp.rol.values_list('id', flat=True))
        return rol_ids
    except Exception:
        return set()


def _get_tutorials_for_page(user, org_pk, url_name):
    """Get active tutorials matching the current page and user roles."""
    if not url_name:
        return []

    user_rol_ids = _get_user_rol_ids(user, org_pk)

    tutorials = Tutorial.objects.filter(
        is_active=True,
    ).prefetch_related('steps', 'target_roles')

    matching = []
    for t in tutorials:
        url_names = [u.strip() for u in t.url_name.split(',')]
        if url_name not in url_names:
            continue
        target_rol_ids = set(t.target_roles.values_list('id', flat=True))
        if target_rol_ids and not target_rol_ids.intersection(user_rol_ids):
            continue
        matching.append(t)

    return matching


@register.simple_tag(takes_context=True)
def tutorial_launcher(context):
    """Renders tutorial engine data and FAB button in base.html."""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return ''

    try:
        profile = request.user.profile
        if not profile.show_tutorials:
            return ''
    except Exception:
        return ''

    org_pk = context.get('org_pk') or (
        request.resolver_match.kwargs.get('org_pk') if request.resolver_match else None
    )
    url_name = (
        request.resolver_match.url_name if request.resolver_match else None
    )

    tutorials = _get_tutorials_for_page(request.user, org_pk, url_name)
    if not tutorials:
        return ''

    dismissed_ids = set(TutorialProgress.objects.filter(
        user=request.user,
        dismissed=True,
    ).values_list('tutorial_id', flat=True))

    completed_ids = set(TutorialProgress.objects.filter(
        user=request.user,
        completed=True,
    ).values_list('tutorial_id', flat=True))

    progress_map = {}
    for tp in TutorialProgress.objects.filter(
        user=request.user,
        tutorial__in=tutorials,
    ):
        progress_map[tp.tutorial_id] = tp.current_step

    tutorials_data = []
    auto_start_slugs = []
    for t in tutorials:
        if t.id in dismissed_ids or t.id in completed_ids:
            continue
        steps = []
        for s in t.steps.all():
            step_data = {
                'key': s.step_key,
                'title': s.title,
                'content': s.content,
                'type': s.step_type,
                'selector': s.css_selector,
                'position': s.position,
                'actionUrl': s.action_url,
            }
            if s.image:
                step_data['imageUrl'] = s.image.url
            steps.append(step_data)
        if not steps:
            continue
        tutorials_data.append({
            'id': t.id,
            'slug': t.slug,
            'title': t.title,
            'description': t.description,
            'steps': steps,
            'currentStep': progress_map.get(t.id, 0),
        })
        if t.auto_start and t.id not in progress_map:
            auto_start_slugs.append(t.slug)

    if not tutorials_data:
        return ''

    config = {
        'tutorials': tutorials_data,
        'autoStart': auto_start_slugs,
        'progressUrl': '/tutorial/api/progress/',
    }

    html = (
        '<script type="text/javascript">'
        'window._tutorialConfig = ' + json.dumps(config, ensure_ascii=False) + ';'
        '</script>'
        '<button class="tutorial-fab" onclick="OrganiLabTutorial.showMenu()" '
        'title="Tutoriales disponibles">?</button>'
    )
    return mark_safe(html)


@register.tag('tutorial_step')
def do_tutorial_step(parser, token):
    """Block tag: {% tutorial_step "slug" "step-key" %}...{% end_tutorial_step %}"""
    bits = token.split_contents()
    if len(bits) != 3:
        raise template.TemplateSyntaxError(
            f"'{bits[0]}' requires 2 arguments: tutorial slug and step key"
        )
    tutorial_slug = bits[1].strip('"\'')
    step_key = bits[2].strip('"\'')
    nodelist = parser.parse(('end_tutorial_step',))
    parser.delete_first_token()
    return TutorialStepNode(nodelist, tutorial_slug, step_key)


class TutorialStepNode(template.Node):
    def __init__(self, nodelist, tutorial_slug, step_key):
        self.nodelist = nodelist
        self.tutorial_slug = tutorial_slug
        self.step_key = step_key

    def render(self, context):
        content = self.nodelist.render(context)
        request = context.get('request')
        if not request or not request.user.is_authenticated:
            return content
        try:
            if not request.user.profile.show_tutorials:
                return content
        except Exception:
            return content
        return (
            f'<div data-tutorial-slug="{self.tutorial_slug}" '
            f'data-tutorial-step="{self.step_key}">'
            f'{content}</div>'
        )


@register.simple_tag()
def tutorial_marker(tutorial_slug, step_key, target_selector=''):
    """Simple tag to mark elements: {% tutorial_marker "slug" "key" "#selector" %}"""
    return mark_safe(
        f'<span class="d-none" data-tutorial-slug="{tutorial_slug}" '
        f'data-tutorial-step="{step_key}" '
        f'data-tutorial-target="{target_selector}"></span>'
    )
