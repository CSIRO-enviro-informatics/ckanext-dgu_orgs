# encoding: utf-8
import logging
from ckan.config.routing import SubMapper
from ckan.exceptions import CkanUrlException
from ckan.lib.helpers import flash_notice
from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IConfigurer, ITemplateHelpers, IRoutes, ISession
from plugins_toolkit import c, add_template_directory, add_public_directory, add_resource, url_for

from ckanext.dgu_orgs.lib.helpers import is_plugin_enabled
from ckanext.dgu_orgs.util import is_bootstrap_2

log = logging.getLogger(__name__)


def get_current_user_id():
    try:
        user_obj = c.userobj
        user_id = user_obj.id
        return user_id
    except (TypeError, AttributeError):
        return None



def delete_routes_by_name(map, route_names):
    if isinstance(route_names, basestring):
        route_names = [route_names]
    for route_name in route_names:
        del map._routenames[route_name]

class DGUOrgsPlugin(SingletonPlugin):
    implements(IConfigurer)
    implements(ITemplateHelpers)
    implements(IRoutes, inherit=True)
    implements(ISession, inherit=True)
    # implements(IReport)

    def get_helpers(self):
        """
        A dictionary of extra helpers that will be available to provide
        dgu specific helpers to the templates.  We may be able to override
        h.linked_user so that we don't need to monkey patch above.
        """
        from ckanext.dgu_orgs.lib import helpers
        from inspect import getmembers, isfunction

        helper_dict = {}

        functions_list = [o for o in getmembers(helpers, isfunction)]
        for name, fn in functions_list:
            if name[0] != '_':
                helper_dict[name] = fn

        return helper_dict

    def before_commit(self, session):
        """
        Before we commit a session we will check to see if any of the new
        items are users so we can notify them to apply for publisher access.
        """
        from pylons.i18n import _
        from ckan.model import User

        session.flush()
        if not hasattr(session, '_object_cache'):
            return

        pubctlr = 'ckanext.dgu_orgs.controllers.organisation:OrganisationController'
        for obj in set(session._object_cache['new']):
            if isinstance(obj, (User)):
                try:
                    url = url_for(controller=pubctlr, action='apply')
                except CkanUrlException:
                    # This occurs when Routes has not yet been initialized
                    # yet, which would be before a WSGI request has been
                    # made. In this case, there will be no flash message
                    # required anyway.
                    return
                return
                #msg = "You can now <a href='%s'>apply for organisation access</a>" % url
                #try:
                #    flash_notice(_(msg), allow_html=True)
                #except TypeError:
                    # Raised when there is no session registered, and this is
                    # the case when using the paster commands.
                    #log.debug('Did not add a flash message due to a missing session: %s' % msg)
                #    pass

    def before_map(self, map):
        map.redirect('/organization/{url:.*}', '/organisation/{url}')
        with SubMapper(map, controller='ckanext.dgu_orgs.controllers.organisation:OrganisationController') as m:
            m.connect('organisation_index',
                     '/organisation', action='index')
            m.connect('organisation_edit',
                     '/organisation/edit/:id', action='edit')
            m.connect('organisation_apply',
                     '/organisation/apply/:id', action='apply')
            m.connect('organisation_apply_empty',
                     '/organisation/apply', action='apply')
            m.connect('organisation_requests',
                     '/organisation/users/requests', action='organisation_requests')
            m.connect('organisation_request',
                     '/organisation/users/request/:token', action='organisation_request')
            m.connect('organisation_request_decision',
                     '/organisation/users/request/:token/:decision',
                     action='organisation_request')
            m.connect('organisation_users',
                    '/organisation/users/:id', action='users')
            m.connect('organisation_new',
                      '/organisation/new', action='new')
            m.connect('/organisation/report_groups_without_admins',
                      action='report_groups_without_admins')
            m.connect('/organisation/report_organisations_and_users',
                      action='report_organisations_and_users')
            m.connect('/organisation/report_users',
                      action='report_users')
            m.connect('/organisation/report_users_not_assigned_to_groups',
                      action='report_users_not_assigned_to_groups')
            m.connect('organisation_read',
                      '/organisation/:id',
                      action='read')

        return map

    def after_map(self, map):
        if is_plugin_enabled('issues'):
            delete_routes_by_name(map, 'issues_for_organization')
            with SubMapper(map, controller='ckanext.issues.controller:IssueController') as m:
                m.connect('issues_for_organization', '/organisation/:org_id/issues', action='issues_for_organization')
        return map

    # def update_config(self, config):
    #     # set the auth profile to use the publisher based auth
    #     config['ckan.auth.profile'] = 'publisher'
    #
    #     # same for the harvesting auth profile
    #     config['ckan.harvest.auth.profile'] = 'publisher'

    # Configurer

    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        # 'templates' is the path to the templates dir, relative to this
        # plugin.py file.

        # first defined templates are higher priority
        if is_bootstrap_2():
            # override some parts with bootstrap2 templates if needed
            add_template_directory(config, 'bs2-templates')
        else:
            add_template_directory(config, 'bs3-templates')

        # This is the template code shared between bs2 and bs3.
        add_template_directory(config, 'templates')

        # Add this plugin's public dir to CKAN's extra_public_paths, so
        # that CKAN will use this plugin's custom static files.
        add_public_directory(config, 'public')

        # Register this plugin's fanstatic directory with CKAN.
        # Here, 'fanstatic' is the path to the fanstatic directory
        # (relative to this plugin.py file), and 'example_theme' is the name
        # that we'll use to refer to this fanstatic directory from CKAN
        # templates.
        add_resource('fanstatic', 'dgu_orgs')

    # # IReport
    #
    # def register_reports(self):
    #     """Register details of an extension's reports"""
    #     from ckanext.dgu_orgs.lib import reports
    #     return [reports.nii_report_info,
    #             reports.publisher_activity_report_info,
    #             reports.publisher_resources_info,
    #             reports.unpublished_report_info,
    #             reports.datasets_without_resources_info,
    #             reports.app_dataset_theme_report_info,
    #             reports.app_dataset_report_info,
    #             reports.admin_editor_info,
    #             reports.licence_report_info,
    #             reports.la_schemas_info,
    #             reports.pdf_datasets_report_info,
    #             reports.html_datasets_report_info,
    #             ]
